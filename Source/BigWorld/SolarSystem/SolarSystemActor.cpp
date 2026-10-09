#include "SolarSystemActor.h"
#include "SolarExplorer.h"
#include "SolarTerrainNoise.h"
#include "WorldScapeRoot.h"
#include "Components/StaticMeshComponent.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/SkyAtmosphereComponent.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "ProceduralMeshComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/WorldSettings.h"
#include "Kismet/GameplayStatics.h"
#include "Math/RotationMatrix.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"
#include "Serialization/JsonSerializer.h"
#include "Dom/JsonObject.h"

namespace
{
FString JsonText(const TSharedRef<FJsonObject>& Object) { FString Text; auto Writer=TJsonWriterFactory<>::Create(&Text); FJsonSerializer::Serialize(Object,Writer); return Text; }
TSharedPtr<FJsonValue> VectorJson(const FVector& V) { TArray<TSharedPtr<FJsonValue>> A; for(int I=0;I<3;++I)A.Add(MakeShared<FJsonValueNumber>(V[I])); return MakeShared<FJsonValueArray>(A); }
bool WriteTGA(const FString& File,int W,int H,const TArray<FColor>& Pixels)
{
    TArray<uint8> Data; Data.SetNumZeroed(18+W*H*4); Data[2]=2; Data[12]=W&255; Data[13]=(W>>8)&255; Data[14]=H&255; Data[15]=(H>>8)&255; Data[16]=32; Data[17]=0x28;
    for(int I=0;I<Pixels.Num();++I){Data[18+I*4]=Pixels[I].B;Data[19+I*4]=Pixels[I].G;Data[20+I*4]=Pixels[I].R;Data[21+I*4]=Pixels[I].A;}
    return FFileHelper::SaveArrayToFile(Data,*File);
}
}

ASolarSystemActor::ASolarSystemActor()
{
    PrimaryActorTick.bCanEverTick=true; PrimaryActorTick.TickGroup=TG_PostUpdateWork;
    RootComponent=CreateDefaultSubobject<USceneComponent>(TEXT("SolarFrame")); RootComponent->SetMobility(EComponentMobility::Movable);
    SunLight=CreateDefaultSubobject<UDirectionalLightComponent>(TEXT("StellarIllumination")); SunLight->SetupAttachment(RootComponent); SunLight->SetMobility(EComponentMobility::Movable);
    SunLight->bAtmosphereSunLight=true; SunLight->AtmosphereSunLightIndex=0; SunLight->SetIntensity(5); SunLight->DynamicShadowDistanceMovableLight=30000;
    LocalAtmosphere=CreateDefaultSubobject<USkyAtmosphereComponent>(TEXT("LocalAtmosphere")); LocalAtmosphere->SetupAttachment(RootComponent);
    LocalAtmosphere->TransformMode=ESkyAtmosphereTransformMode::PlanetCenterAtComponentTransform;
    LocalAtmosphere->SetVisibility(false);
    Trees=CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(TEXT("TemperateForest")); Trees->SetupAttachment(RootComponent); Trees->SetCollisionEnabled(ECollisionEnabled::NoCollision); Trees->SetMobility(EComponentMobility::Movable);
    Grass=CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(TEXT("SurfaceGrass")); Grass->SetupAttachment(RootComponent); Grass->SetCollisionEnabled(ECollisionEnabled::NoCollision); Grass->SetMobility(EComponentMobility::Movable);
    Bodies=SolarModel::Defaults();
}

void ASolarSystemActor::BeginPlay()
{
    Super::BeginPlay(); GetWorld()->GetWorldSettings()->bEnableWorldBoundsChecks=false;
    CreateVisuals(); SolarModel::Evaluate(Bodies,SimulationSeconds,Positions,Rotations);
}

void ASolarSystemActor::PostRegisterAllComponents()
{
    Super::PostRegisterAllComponents();
#if WITH_EDITOR
    if(!IsTemplate() && GetWorld() && !GetWorld()->IsGameWorld() && Bodies.Num()==10)
        PreviewSystem();
#endif
}

void ASolarSystemActor::RebuildPreview()
{
    if(GetWorld() && GetWorld()->IsGameWorld())return;
    for(const auto& C:Spheres)if(C)C->DestroyComponent();
    for(const auto& C:Shells)if(C)C->DestroyComponent();
    if(Clouds)Clouds->DestroyComponent();
    if(Rings)Rings->DestroyComponent();
    Spheres.Empty();Shells.Empty();SurfaceMIDs.Empty();ShellMIDs.Empty();
    Clouds=nullptr;Rings=nullptr;CloudMID=nullptr;RingMID=nullptr;
    PreviewSystem();
}

void ASolarSystemActor::CreateVisuals()
{
    if(Spheres.Num()==Bodies.Num())return;
    UStaticMesh* Sphere=PlanetMesh?PlanetMesh.Get():LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Sphere.Sphere"));
    auto AddSphere=[&](FName Name,UMaterialInterface* Mat)
    {
        auto* C=NewObject<UStaticMeshComponent>(this,MakeUniqueObjectName(this,UStaticMeshComponent::StaticClass(),Name),RF_Transient); C->SetupAttachment(RootComponent); C->SetStaticMesh(Sphere); C->SetMobility(EComponentMobility::Movable); C->SetCollisionEnabled(ECollisionEnabled::NoCollision); C->SetCastShadow(false); C->SetMaterial(0,Mat); C->RegisterComponent(); return C;
    };
    for(int I=0;I<Bodies.Num();++I)
    {
        auto* M=BodyMaterials.IsValidIndex(I)&&BodyMaterials[I]?UMaterialInstanceDynamic::Create(BodyMaterials[I],this):nullptr;
        SurfaceMIDs.Add(M); Spheres.Add(AddSphere(FName(*("Body_"+Bodies[I].Key)),M));
        auto* A=AtmosphereMaterial?UMaterialInstanceDynamic::Create(AtmosphereMaterial,this):nullptr;
        if(A) A->SetVectorParameterValue(TEXT("Tint"),I==2?FLinearColor(.65,.37,.09):I==5?FLinearColor(.4,.13,.045):FLinearColor(.07,.28,.75));
        ShellMIDs.Add(A); Shells.Add(AddSphere(FName(*("Atmosphere_"+Bodies[I].Key)),A));
    }
    CloudMID=CloudMaterial?UMaterialInstanceDynamic::Create(CloudMaterial,this):nullptr;
    Clouds=AddSphere(TEXT("EarthCloudDeck"),CloudMID);
    Rings=NewObject<UProceduralMeshComponent>(this,TEXT("SaturnRings"),RF_Transient); Rings->SetupAttachment(RootComponent); Rings->SetMobility(EComponentMobility::Movable); Rings->SetCollisionEnabled(ECollisionEnabled::NoCollision); Rings->SetCastShadow(false); Rings->RegisterComponent();
    TArray<FVector> V,N; TArray<int32> Tri; TArray<FVector2D> UV; TArray<FLinearColor> Col; TArray<FProcMeshTangent> Tan;
    constexpr int Segments=384;
    // Inner C ring through outer A ring; real radius ratios and Cassini gap in material.
    for(int I=0;I<=Segments;++I)for(int Side=0;Side<2;++Side)
    {
        double A=2*PI*I/Segments,R=Side?140220./58232.:74658./58232.; V.Add(FVector(FMath::Cos(A)*R,FMath::Sin(A)*R,0)); N.Add(FVector::UpVector); UV.Add(FVector2D(Side,double(I)/Segments));
    }
    for(int I=0;I<Segments;++I){int A=I*2;Tri.Append({A,A+2,A+1,A+1,A+2,A+3});}
    Rings->CreateMeshSection_LinearColor(0,V,Tri,N,UV,Col,Tan,false);
    RingMID=RingMaterial?UMaterialInstanceDynamic::Create(RingMaterial,this):nullptr; Rings->SetMaterial(0,RingMID);
    Trees->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/WorldScape/Ressources/Mesh/Tree/SM_Tree_1.SM_Tree_1")));
    Grass->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/WorldScape/Ressources/Mesh/Grass/SM_Grass_Temp.SM_Grass_Temp")));
    Trees->SetCullDistances(180000,260000); Grass->SetCullDistances(12000,24000);
}

void ASolarSystemActor::PreviewSystem()
{
    CreateVisuals(); SolarModel::Evaluate(Bodies,SimulationSeconds,Positions,Rotations);
    UpdateVisuals(FVector(Bodies[FocusIndex].RadiusKm*2.8*SolarModel::CmPerKm,0,0));
}

void ASolarSystemActor::ClearTerrain()
{
    if(ActiveTerrain) { ActiveTerrain->Destroy(); ActiveTerrain=nullptr; }
    ActiveNoise=nullptr; Trees->ClearInstances(); Grass->ClearInstances(); bSurfaceMode=false; LocalAtmosphere->SetVisibility(false);
}

void ASolarSystemActor::FocusBody(int32 Index)
{
    if(!Bodies.IsValidIndex(Index))return;
    ClearTerrain(); FocusIndex=Index; SolarModel::Evaluate(Bodies,SimulationSeconds,Positions,Rotations);
    if(auto* P=Cast<ASolarExplorerPawn>(UGameplayStatics::GetPlayerPawn(this,0)))
    {
        const FVector Light=GetFocusSunDirection();
        FVector ViewDir=(Light*.84+FVector::UpVector*.35+FVector::CrossProduct(Light,FVector::UpVector)*.32).GetSafeNormal();
        if(Index==0)ViewDir=FVector(1,0,.22).GetSafeNormal();
        const double Distance=Bodies[Index].RadiusKm*(Index==7?6.5:4.3)*SolarModel::CmPerKm;
        const FVector Location=ViewDir*Distance;
        P->SetViewPose(Location,FRotationMatrix::MakeFromXZ(-ViewDir,FVector::UpVector).Rotator());
        P->SpeedKmPerSecond=FMath::Max(10.,Bodies[Index].RadiusKm*.08);
    }
    bInitialized=true;
}

FVector ASolarSystemActor::GetFocusSunDirection() const
{
    if(!Positions.IsValidIndex(FocusIndex)||!Rotations.IsValidIndex(FocusIndex)||FocusIndex==0)return FVector(1,0,0);
    return Rotations[FocusIndex].UnrotateVector(-Positions[FocusIndex]).GetSafeNormal();
}
double ASolarSystemActor::GetGroundRadiusKm(const FVector& N) const
{
    return Bodies[FocusIndex].RadiusKm+FMath::Max(Bodies[FocusIndex].bOcean?0.:-100.,SolarModel::HeightKm(FocusIndex,N));
}
FVector ASolarSystemActor::GetLogicalPositionKm() const
{
    const APawn* P=UGameplayStatics::GetPlayerPawn(this,0);
    return Positions.IsValidIndex(FocusIndex)?Positions[FocusIndex]+Rotations[FocusIndex].RotateVector(P?P->GetActorLocation()/SolarModel::CmPerKm:FVector::ZeroVector):FVector::ZeroVector;
}

bool ASolarSystemActor::VisitSurface(double LatitudeDeg,double LongitudeDeg,double HeightMeters)
{
    if(!Bodies.IsValidIndex(FocusIndex)||!Bodies[FocusIndex].bSolid)return false;
    auto* P=Cast<ASolarExplorerPawn>(UGameplayStatics::GetPlayerPawn(this,0)); if(!P)return false;
    const bool DefaultSite=LatitudeDeg==25 && LongitudeDeg==0;
    FVector N(FMath::Cos(FMath::DegreesToRadians(LatitudeDeg))*FMath::Cos(FMath::DegreesToRadians(LongitudeDeg)),FMath::Cos(FMath::DegreesToRadians(LatitudeDeg))*FMath::Sin(FMath::DegreesToRadians(LongitudeDeg)),FMath::Sin(FMath::DegreesToRadians(LatitudeDeg)));
    if(DefaultSite)
    {
        double Best=-1e9; const FVector Sun=GetFocusSunDirection();
        for(int I=0;I<1536;++I)
        {
            const double Z=1-2*(I+.5)/1536.,A=I*2.399963229728653;
            const FVector D(FMath::Sqrt(1-Z*Z)*FMath::Cos(A),FMath::Sqrt(1-Z*Z)*FMath::Sin(A),Z);
            const double H=SolarModel::HeightKm(FocusIndex,D);
            const double Suitability=(FocusIndex==3?(H>.04&&H<1.5&&FMath::Abs(Z)<.72?3.:-10.):0)+FVector::DotProduct(D,Sun)-FMath::Abs(H)*.05;
            if(Suitability>Best){Best=Suitability;N=D;}
        }
    }
    ClearTerrain();
    const FVector Location=N*(GetGroundRadiusKm(N)+FMath::Max(.005,HeightMeters*.001))*SolarModel::CmPerKm;
    FVector East=FVector::CrossProduct(FVector::UpVector,N).GetSafeNormal(1e-9,FVector::RightVector);
    P->SetViewPose(Location,FRotationMatrix::MakeFromXZ((East-N*.12).GetSafeNormal(),N).Rotator()); P->SpeedKmPerSecond=.08;
    FTransform Transform(FQuat::Identity,FVector::ZeroVector);
    ActiveTerrain=GetWorld()->SpawnActorDeferred<AWorldScapeRoot>(AWorldScapeRoot::StaticClass(),Transform,this,nullptr,ESpawnActorCollisionHandlingMethod::AlwaysSpawn);
    if(!ActiveTerrain)return false;
    ActiveTerrain->PlanetScale=Bodies[FocusIndex].RadiusKm*SolarModel::CmPerKm;
    ActiveTerrain->GenerationType=EWorldScapeType::Planet;
    ActiveTerrain->bGenerateWorldScape=true; ActiveTerrain->bOcean=Bodies[FocusIndex].bOcean;
    ActiveTerrain->MaxLod=13; ActiveTerrain->LodResolution=96; ActiveTerrain->TriangleSize=400; ActiveTerrain->HeightAnchor=15000;
    ActiveTerrain->OceanMaxLod=13; ActiveTerrain->OceanLodResolution=48; ActiveTerrain->OceanTriangleSize=800;
    ActiveTerrain->NoiseIntensity=850000; ActiveTerrain->bProjectPosition=false; ActiveTerrain->bGenerateCollision=false; ActiveTerrain->bGenerateCollisionInEditor=false;
    ActiveTerrain->Foliages.Empty(); ActiveTerrain->DistanceToFreezeGeneration=ActiveTerrain->PlanetScale*100;
    ActiveNoise=NewObject<USolarTerrainNoise>(ActiveTerrain); ActiveNoise->BodyIndex=FocusIndex; ActiveTerrain->WorldScapeNoise=ActiveNoise;
    if(TerrainMaterials.IsValidIndex(FocusIndex))ActiveTerrain->TerrainMaterial.DefaultMaterial=TerrainMaterials[FocusIndex];
    ActiveTerrain->OceanMaterial.DefaultMaterial=OceanMaterial;
    UGameplayStatics::FinishSpawningActor(ActiveTerrain,Transform);
    bSurfaceMode=true;
    LocalAtmosphere->SetBottomRadius(Bodies[FocusIndex].RadiusKm);
    LocalAtmosphere->SetAtmosphereHeight(FMath::Max(1.,Bodies[FocusIndex].AtmosphereKm));
    LocalAtmosphere->SetRayleighScattering(FocusIndex==5?FLinearColor(.016,.006,.003):FocusIndex==2?FLinearColor(.025,.017,.006):FLinearColor(.005802,.013558,.0331));
    LocalAtmosphere->SetRayleighScatteringScale(FocusIndex==5?.08:1);
    LocalAtmosphere->SetMieScatteringScale(FocusIndex==2?.04f:FocusIndex==5?.0002f:.003996f);
    LocalAtmosphere->SetVisibility(Bodies[FocusIndex].AtmosphereKm>0);
    BuildVegetation(N); return true;
}

void ASolarSystemActor::BuildVegetation(const FVector& N)
{
    Trees->ClearInstances(); Grass->ClearInstances(); VegetationCenter=N*Bodies[FocusIndex].RadiusKm*SolarModel::CmPerKm;
    if(FocusIndex!=3)return;
    const FVector X=FVector::CrossProduct(N,FVector::UpVector).GetSafeNormal(1e-9,FVector::ForwardVector),Y=FVector::CrossProduct(N,X);
    FRandomStream Random(917+FMath::FloorToInt(N.X*1000)+FMath::FloorToInt(N.Y*1000)*79);
    for(int I=0;I<1500;++I)
    {
        const double A=Random.FRand()*2*PI,R=FMath::Sqrt(Random.FRand())*(I<700?160000:18000);
        const FVector D=(VegetationCenter+X*FMath::Cos(A)*R+Y*FMath::Sin(A)*R).GetSafeNormal();
        const double H=SolarModel::HeightKm(3,D);
        if(H<.015||H>2.0||FMath::Abs(D.Z)>.86)continue;
        const FQuat Q=FRotationMatrix::MakeFromZ(D).ToQuat()*FQuat(FVector::UpVector,Random.FRand()*2*PI);
        const FVector Loc=D*(Bodies[3].RadiusKm+H)*SolarModel::CmPerKm;
        const double Scale=I<700?Random.FRandRange(.75,1.5):Random.FRandRange(.8,1.6);
        (I<700?Trees:Grass)->AddInstance(FTransform(Q,Loc,FVector(Scale)),true);
    }
}

void ASolarSystemActor::SetSimulationTime(double Seconds) { if(FMath::IsFinite(Seconds))SimulationSeconds=Seconds; SolarModel::Evaluate(Bodies,SimulationSeconds,Positions,Rotations); }
void ASolarSystemActor::SetTimeScale(double Scale) { if(FMath::IsFinite(Scale))TimeScale=FMath::Clamp(Scale,0.,100000.); }

void ASolarSystemActor::Tick(float Dt)
{
    Super::Tick(Dt);
    if(!GetWorld()->IsGameWorld())
    {
        if(Bodies.Num()==10)PreviewSystem();
        return;
    }
    APawn* P=UGameplayStatics::GetPlayerPawn(this,0); if(!P)return;
    if(!bInitialized)FocusBody(FocusIndex);
    SimulationSeconds+=double(Dt)*TimeScale; SolarModel::Evaluate(Bodies,SimulationSeconds,Positions,Rotations);
    const double Alt=P->GetActorLocation().Size()/SolarModel::CmPerKm-Bodies[FocusIndex].RadiusKm;
    if(bSurfaceMode && Alt>220)ClearTerrain();
    if(!bSurfaceMode && Bodies[FocusIndex].bSolid && Alt<70)
    {
        const FVector N=P->GetActorLocation().GetSafeNormal();
        VisitSurface(FMath::RadiansToDegrees(FMath::Asin(N.Z)),FMath::RadiansToDegrees(FMath::Atan2(N.Y,N.X)),FMath::Max(10.,(Alt-SolarModel::HeightKm(FocusIndex,N))*1000));
    }
    if(bSurfaceMode && FocusIndex==3)
    {
        VegetationTimer+=Dt;
        if(VegetationTimer>2 && Alt<4)
        {
            VegetationTimer=0; const FVector N=P->GetActorLocation().GetSafeNormal();
            if(FVector::Dist(N*Bodies[3].RadiusKm*SolarModel::CmPerKm,VegetationCenter)>65000)BuildVegetation(N);
        }
        Trees->SetVisibility(Alt<4); Grass->SetVisibility(Alt<1);
    }
    UpdateVisuals(P->GetActorLocation());
}

void ASolarSystemActor::UpdateVisuals(const FVector& ObserverLocalCm)
{
    if(!Rotations.IsValidIndex(FocusIndex)||Spheres.Num()!=Bodies.Num())return;
    const FQuat FrameInv=Rotations[FocusIndex].Inverse();
    // Distant meshes preserve angular size; physics/catalogue coordinates remain in km.
    // The near body's world remains strictly 1 cm per Unreal unit.
    const double FarLimit=FMath::Max(2e10,ObserverLocalCm.Size()*6);
    for(int I=0;I<Bodies.Num();++I)
    {
        FVector Center=FrameInv.RotateVector(Positions[I]-Positions[FocusIndex])*SolarModel::CmPerKm;
        double Scale=1;
        if(I!=FocusIndex) { const double Distance=(Center-ObserverLocalCm).Size(); Scale=FMath::Min(1.,FarLimit/FMath::Max(1.,Distance)); Center=ObserverLocalCm+(Center-ObserverLocalCm)*Scale; }
        const FQuat Q=FrameInv*Rotations[I]; const double R=Bodies[I].RadiusKm*SolarModel::CmPerKm*Scale;
        Spheres[I]->SetWorldLocationAndRotation(Center,Q); Spheres[I]->SetWorldScale3D(FVector(R/50));
        Spheres[I]->SetVisibility(!(I==FocusIndex&&bSurfaceMode));
        const FVector SunLocal=I==0?FVector::UpVector:Rotations[I].UnrotateVector(-Positions[I]).GetSafeNormal();
        if(SurfaceMIDs[I])SurfaceMIDs[I]->SetVectorParameterValue(TEXT("SunDirection"),FLinearColor(SunLocal.X,SunLocal.Y,SunLocal.Z));
        Shells[I]->SetWorldLocationAndRotation(Center,Q); Shells[I]->SetWorldScale3D(FVector((R+Bodies[I].AtmosphereKm*SolarModel::CmPerKm*Scale)/50));
        Shells[I]->SetVisibility(Bodies[I].AtmosphereKm>0 && !(I==FocusIndex&&bSurfaceMode));
        if(ShellMIDs[I])ShellMIDs[I]->SetVectorParameterValue(TEXT("SunDirection"),FLinearColor(SunLocal.X,SunLocal.Y,SunLocal.Z));
        if(I==3) { Clouds->SetWorldLocationAndRotation(Center,Q); Clouds->SetWorldScale3D(FVector((R+1000000*Scale)/50)); Clouds->SetVisibility(!(I==FocusIndex&&bSurfaceMode)); if(CloudMID)CloudMID->SetVectorParameterValue(TEXT("SunDirection"),FLinearColor(SunLocal.X,SunLocal.Y,SunLocal.Z)); }
        if(I==7) { Rings->SetWorldLocationAndRotation(Center,Q); Rings->SetWorldScale3D(FVector(R)); if(RingMID)RingMID->SetVectorParameterValue(TEXT("SunDirection"),FLinearColor(SunLocal.X,SunLocal.Y,SunLocal.Z)); }
    }
    const FVector Light=GetFocusSunDirection(); SunLight->SetWorldRotation((-Light).Rotation());
    const double DistanceAU=FMath::Max(.2,Positions[FocusIndex].Size()/SolarModel::AU);
    SunLight->SetIntensity(FocusIndex==0?0:5/FMath::Square(DistanceAU));
    SunLight->LightSourceAngle=FocusIndex==0?.535:FMath::RadiansToDegrees(2*FMath::Atan(Bodies[0].RadiusKm/FMath::Max(1.,Positions[FocusIndex].Size())));
}

bool ASolarSystemActor::ExportProceduralTextures(const FString& Directory,int32 Width)
{
    const int W=FMath::Clamp(Width,256,4096),H=W/2; IFileManager::Get().MakeDirectory(*Directory,true);
    TArray<FColor> Pixels; Pixels.SetNum(W*H);
    for(int Body=0;Body<Bodies.Num();++Body)
    {
        for(int Y=0;Y<H;++Y)for(int X=0;X<W;++X)
        {
            const double Lat=PI/2-PI*(Y+.5)/H,Lon=2*PI*(X+.5)/W-PI;
            const FVector N(FMath::Cos(Lat)*FMath::Cos(Lon),FMath::Cos(Lat)*FMath::Sin(Lon),FMath::Sin(Lat));
            Pixels[Y*W+X]=SolarModel::SurfaceColor(Body,N).ToFColorSRGB();
        }
        if(!WriteTGA(FPaths::Combine(Directory,"T_"+Bodies[Body].Key+".tga"),W,H,Pixels))return false;
    }
    for(int Y=0;Y<H;++Y)for(int X=0;X<W;++X)
    {
        const double Lat=PI/2-PI*(Y+.5)/H,Lon=2*PI*(X+.5)/W-PI;
        const FVector N(FMath::Cos(Lat)*FMath::Cos(Lon),FMath::Cos(Lat)*FMath::Sin(Lon),FMath::Sin(Lat));
        const uint8 C=FMath::Clamp(FMath::RoundToInt(SolarModel::CloudDensity(N)*255),0,255); Pixels[Y*W+X]=FColor(C,C,C,255);
    }
    return WriteTGA(FPaths::Combine(Directory,TEXT("T_Clouds.tga")),W,H,Pixels);
}

FString ASolarSystemActor::GetDiagnostics() const
{
    auto Root=MakeShared<FJsonObject>(); Root->SetNumberField(TEXT("focus"),FocusIndex);Root->SetNumberField(TEXT("simulation_seconds"),SimulationSeconds);Root->SetNumberField(TEXT("time_scale"),TimeScale);Root->SetBoolField(TEXT("surface_mode"),bSurfaceMode);
    Root->SetField(TEXT("logical_position_km"),VectorJson(GetLogicalPositionKm()));Root->SetNumberField(TEXT("trees"),Trees->GetInstanceCount());Root->SetNumberField(TEXT("grass"),Grass->GetInstanceCount());Root->SetBoolField(TEXT("atmosphere"),LocalAtmosphere->IsVisible());
    TArray<TSharedPtr<FJsonValue>> Rows;
    for(int I=0;I<Bodies.Num();++I) { auto B=MakeShared<FJsonObject>();B->SetStringField(TEXT("key"),Bodies[I].Key);B->SetNumberField(TEXT("radius_km"),Bodies[I].RadiusKm); B->SetNumberField(TEXT("semi_major_axis_km"),Bodies[I].SemiMajorAxisKm);B->SetNumberField(TEXT("period_days"),Bodies[I].PeriodDays);B->SetBoolField(TEXT("tidal_lock"),Bodies[I].bTidalLock);B->SetNumberField(TEXT("atmosphere_km"),Bodies[I].AtmosphereKm);if(Positions.IsValidIndex(I))B->SetField(TEXT("position_km"),VectorJson(Positions[I]));Rows.Add(MakeShared<FJsonValueObject>(B)); }
    Root->SetArrayField(TEXT("bodies"),Rows);return JsonText(Root);
}

FString ASolarSystemActor::ValidateModel() const
{
    auto Report=MakeShared<FJsonObject>(); TArray<TSharedPtr<FJsonValue>> Failures;
    auto Check=[&](bool Pass,const TCHAR* Message){if(!Pass)Failures.Add(MakeShared<FJsonValueString>(Message));};
    Check(Bodies.Num()==10,TEXT("Catalogue must contain the Sun, eight planets and Moon"));
    for(const FSolarBody& B:Bodies)if(B.SemiMajorAxisKm>0)
    {
        FSolarBody Test=B;Test.MeanAnomalyDeg=0;
        Check(FMath::Abs(SolarModel::OrbitPosition(Test,0).Size()-B.SemiMajorAxisKm*(1-B.Eccentricity))<.001,TEXT("Periapsis radius"));
        Check(FMath::Abs(SolarModel::OrbitPosition(Test,B.PeriodDays*43200).Size()-B.SemiMajorAxisKm*(1+B.Eccentricity))<.001,TEXT("Apoapsis radius"));
        Check(FVector::Dist(SolarModel::OrbitPosition(B,0),SolarModel::OrbitPosition(B,B.PeriodDays*86400))<.001,TEXT("Orbit closure"));
    }
    for(int Step=0;Step<20;++Step)
    {
        TArray<FVector> P;TArray<FQuat> Q;SolarModel::Evaluate(Bodies,Step*112233.,P,Q);
        Check(FVector::DotProduct(Q[4].GetForwardVector(),(P[3]-P[4]).GetSafeNormal())>1-1e-10,TEXT("Moon must face Earth"));
        const FVector Local(6371.0084,.002,.003),Global=P[3]+Q[3].RotateVector(Local);
        Check(FVector::Dist(Q[3].UnrotateVector(Global-P[3]),Local)<1e-6,TEXT("Local/inertial coordinate roundtrip"));
    }
    int Invalid=0,Water=0;
    for(int I=0;I<512;++I)
    {
        const double Z=1-2*(I+.5)/512.,A=I*2.399963229728653;const FVector N(FMath::Sqrt(1-Z*Z)*FMath::Cos(A),FMath::Sqrt(1-Z*Z)*FMath::Sin(A),Z);
        const double H=SolarModel::HeightKm(3,N);Water+=H<0;
        for(int B=1;B<=5;++B)Invalid+=!FMath::IsFinite(SolarModel::HeightKm(B,N));
    }
    Check(Invalid==0,TEXT("Terrain finite samples"));Check(Water>200&&Water<475,TEXT("Earth has both substantial oceans and land"));
    Check(SolarModel::HeightKm(3,FVector::UpVector)>0&&SolarModel::HeightKm(3,-FVector::UpVector)>0,TEXT("Both polar ice caps above sea level"));
    Report->SetArrayField(TEXT("failures"),Failures);Report->SetBoolField(TEXT("success"),Failures.IsEmpty());Report->SetNumberField(TEXT("earth_water_fraction"),Water/512.);Report->SetNumberField(TEXT("terrain_invalid"),Invalid);return JsonText(Report);
}
