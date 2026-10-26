#include "SolarSystemActor.h"
#include "SolarExplorer.h"
#include "SolarTerrainNoise.h"
#include "WorldScapeRoot.h"
#include "Components/StaticMeshComponent.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/SkyLightComponent.h"
#include "Components/PostProcessComponent.h"
#include "Components/SkyAtmosphereComponent.h"
#include "Components/VolumetricCloudComponent.h"
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
    SunLight->bAtmosphereSunLight=true; SunLight->AtmosphereSunLightIndex=0; SunLight->SetIntensity(SolarIlluminanceAtOneAU); SunLight->DynamicShadowDistanceMovableLight=30000;
    SurfaceSkyLight=CreateDefaultSubobject<USkyLightComponent>(TEXT("SurfaceSkyLight"));
    SurfaceSkyLight->SetupAttachment(RootComponent); SurfaceSkyLight->SetMobility(EComponentMobility::Movable);
    SurfaceSkyLight->CubemapResolution=64; SurfaceSkyLight->bLowerHemisphereIsBlack=false;
    SurfaceSkyLight->SetRealTimeCaptureEnabled(true); SurfaceSkyLight->SetIntensity(0);
    LightingExposure=CreateDefaultSubobject<UPostProcessComponent>(TEXT("LightingExposure"));
    LightingExposure->SetupAttachment(RootComponent); LightingExposure->bUnbound=true; LightingExposure->Priority=100;
    auto& Exposure=LightingExposure->Settings;
    Exposure.bOverride_AutoExposureMethod=true; Exposure.AutoExposureMethod=AEM_Manual;
    Exposure.bOverride_AutoExposureApplyPhysicalCameraExposure=true; Exposure.AutoExposureApplyPhysicalCameraExposure=true;
    Exposure.bOverride_CameraISO=true; Exposure.CameraISO=100;
    Exposure.bOverride_CameraShutterSpeed=true; Exposure.CameraShutterSpeed=125;
    Exposure.bOverride_DepthOfFieldFstop=true; Exposure.DepthOfFieldFstop=16;
    Exposure.bOverride_AutoExposureBias=true; Exposure.AutoExposureBias=0;
    Exposure.bOverride_AutoExposureBiasCurve=true; Exposure.AutoExposureBiasCurve=nullptr;
    Exposure.bOverride_LocalExposureHighlightContrastScale=true; Exposure.LocalExposureHighlightContrastScale=1;
    Exposure.bOverride_LocalExposureShadowContrastScale=true; Exposure.LocalExposureShadowContrastScale=1;
    LocalAtmosphere=CreateDefaultSubobject<USkyAtmosphereComponent>(TEXT("LocalAtmosphere")); LocalAtmosphere->SetupAttachment(RootComponent);
    LocalAtmosphere->TransformMode=ESkyAtmosphereTransformMode::PlanetCenterAtComponentTransform;
    LocalAtmosphere->SetVisibility(false);
    VolumeClouds=CreateDefaultSubobject<UVolumetricCloudComponent>(TEXT("PlanetaryCloudVolume")); VolumeClouds->SetupAttachment(RootComponent);
    VolumeClouds->SetVisibility(false);
    Trees=CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(TEXT("TemperateForest")); Trees->SetupAttachment(RootComponent); Trees->SetCollisionEnabled(ECollisionEnabled::NoCollision); Trees->SetMobility(EComponentMobility::Movable);
    Grass=CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(TEXT("SurfaceGrass")); Grass->SetupAttachment(RootComponent); Grass->SetCollisionEnabled(ECollisionEnabled::NoCollision); Grass->SetMobility(EComponentMobility::Movable);
    Bodies=SolarModel::Defaults();
}

void ASolarSystemActor::BeginPlay()
{
    Super::BeginPlay(); GetWorld()->GetWorldSettings()->bEnableWorldBoundsChecks=false;
    CreateVisuals(); SolarModel::Evaluate(Bodies,SimulationSeconds,Positions,Rotations);
    SunLight->bPerPixelAtmosphereTransmittance=true;
    SunLight->MarkRenderStateDirty();
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
    for(const auto& C:PlanetRings)if(C)C->DestroyComponent();
    Spheres.Empty();Shells.Empty();SurfaceMIDs.Empty();ShellMIDs.Empty();
    Clouds=nullptr;CloudMID=nullptr;PlanetRings.Empty();RingMIDs.Empty();
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
    if(VolumeCloudMaterial)
    {
        VolumeCloudMID=UMaterialInstanceDynamic::Create(VolumeCloudMaterial,this);
        VolumeClouds->SetMaterial(VolumeCloudMID);
    }
    PlanetRings.SetNum(Bodies.Num()); RingMIDs.SetNum(Bodies.Num());
    // Keep the existing annulus approach. All four planets share one shader;
    // geometry encloses each profile, while opacity resolves the individual bands.
    const double InnerKm[]={122900.,74400.,41000.,40800.};
    const double OuterKm[]={280100.,140600.,107000.,63200.};
    for(int Body=6;Body<10 && Body<Bodies.Num();++Body)
    {
        auto* Ring=NewObject<UProceduralMeshComponent>(this,MakeUniqueObjectName(this,UProceduralMeshComponent::StaticClass(),FName(*(Bodies[Body].Key+TEXT("Rings")))),RF_Transient);
        Ring->SetupAttachment(RootComponent);Ring->SetMobility(EComponentMobility::Movable);
        Ring->SetCollisionEnabled(ECollisionEnabled::NoCollision);Ring->SetCastShadow(false);Ring->RegisterComponent();
        TArray<FVector> V,N;TArray<int32> Tri;TArray<FVector2D> UV;TArray<FLinearColor> Col;TArray<FProcMeshTangent> Tan;
        constexpr int Segments=1024;
        for(int I=0;I<=Segments;++I)for(int Side=0;Side<2;++Side)
        {
            const double A=2*PI*I/Segments,R=(Side?OuterKm[Body-6]:InnerKm[Body-6])/Bodies[Body].RadiusKm;
            V.Add(FVector(FMath::Cos(A)*R,FMath::Sin(A)*R,0));N.Add(FVector::UpVector);UV.Add(FVector2D(Side,double(I)/Segments));
        }
        for(int I=0;I<Segments;++I){int A=I*2;Tri.Append({A,A+2,A+1,A+1,A+2,A+3});}
        Ring->CreateMeshSection_LinearColor(0,V,Tri,N,UV,Col,Tan,false);
        auto* MID=RingMaterial?UMaterialInstanceDynamic::Create(RingMaterial,this):nullptr;
        if(MID)
        {
            MID->SetScalarParameterValue(TEXT("BodyIndex"),Body);
            MID->SetScalarParameterValue(TEXT("InnerRadiusKm"),InnerKm[Body-6]);
            MID->SetScalarParameterValue(TEXT("OuterRadiusKm"),OuterKm[Body-6]);
            MID->SetScalarParameterValue(TEXT("RadiusKm"),Bodies[Body].RadiusKm);
        }
        Ring->SetMaterial(0,MID);PlanetRings[Body]=Ring;RingMIDs[Body]=MID;
    }
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
    ActiveNoise=nullptr; TerrainMID=nullptr; OceanMID=nullptr;
    Trees->ClearInstances(); Grass->ClearInstances(); bSurfaceMode=false; TerrainBlend=0; TerrainWarmup=0;
}

void ASolarSystemActor::ResetCatalogue() { Bodies=SolarModel::Defaults(); AtmosphereFocus=INDEX_NONE; }
float ASolarSystemActor::GetCloudCoverage(FVector Direction) const { return SolarModel::CloudDensity(Direction.GetSafeNormal()); }

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
        const FVector EclipticUp=Rotations[Index].UnrotateVector(FVector::UpVector);
        P->SetViewPose(Location,FRotationMatrix::MakeFromXZ(-ViewDir,EclipticUp).Rotator());
        P->SpeedKmPerSecond=FMath::Max(10.,Bodies[Index].RadiusKm*.08);
    }
    bInitialized=true;
    ConfigureAtmosphere();
}

bool ASolarSystemActor::ReframeBody(int32 Index)
{
    if(!Bodies.IsValidIndex(Index)||Index==FocusIndex)return false;
    auto* P=Cast<ASolarExplorerPawn>(UGameplayStatics::GetPlayerPawn(this,0)); if(!P)return false;
    // Re-express the same inertial pose in the new body-fixed frame. No teleport.
    const FVector Inertial=GetLogicalPositionKm();
    const FQuat InertialRotation=Rotations[FocusIndex]*P->GetActorQuat();
    ClearTerrain(); FocusIndex=Index;
    P->SetViewPose(Rotations[Index].UnrotateVector(Inertial-Positions[Index])*SolarModel::CmPerKm,(Rotations[Index].Inverse()*InertialRotation).Rotator());
    ConfigureAtmosphere(); return true;
}

FVector ASolarSystemActor::GetFocusSunDirection() const
{
    if(!Positions.IsValidIndex(FocusIndex)||!Rotations.IsValidIndex(FocusIndex)||FocusIndex==0)return FVector(1,0,0);
    return Rotations[FocusIndex].UnrotateVector(-Positions[FocusIndex]).GetSafeNormal();
}
double ASolarSystemActor::GetGroundRadiusKm(const FVector& N) const
{
    // Solid terrain includes the seabed. Water is traversable by the explorer.
    return Bodies[FocusIndex].RadiusKm+FMath::Max(-100.,SolarModel::HeightKm(FocusIndex,N));
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
    // Surface bookmarks still arrive above water; normal flight can enter it.
    const double ArrivalRadius=Bodies[FocusIndex].bOcean?FMath::Max(Bodies[FocusIndex].RadiusKm,GetGroundRadiusKm(N)):GetGroundRadiusKm(N);
    const FVector Location=N*(ArrivalRadius+FMath::Max(.005,HeightMeters*.001))*SolarModel::CmPerKm;
    FVector East=FVector::CrossProduct(FVector::UpVector,N).GetSafeNormal(1e-9,FVector::RightVector);
    P->SetViewPose(Location,FRotationMatrix::MakeFromXZ((East-N*.12).GetSafeNormal(),N).Rotator()); P->SpeedKmPerSecond=.08;
    EnsureTerrain(); ConfigureAtmosphere(); BuildVegetation(N); return ActiveTerrain!=nullptr;
}

void ASolarSystemActor::EnsureTerrain()
{
    if(ActiveTerrain||!Bodies[FocusIndex].bSolid)return;
    FTransform Transform(FQuat::Identity,FVector::ZeroVector);
    ActiveTerrain=GetWorld()->SpawnActorDeferred<AWorldScapeRoot>(AWorldScapeRoot::StaticClass(),Transform,this,nullptr,ESpawnActorCollisionHandlingMethod::AlwaysSpawn);
    if(!ActiveTerrain)return;
    ActiveTerrain->PlanetScale=Bodies[FocusIndex].RadiusKm*SolarModel::CmPerKm;
    ActiveTerrain->GenerationType=EWorldScapeType::Planet;
    ActiveTerrain->bGenerateWorldScape=true; ActiveTerrain->bOcean=Bodies[FocusIndex].bOcean;
    ActiveTerrain->MaxLod=16; ActiveTerrain->LodResolution=128; ActiveTerrain->TriangleSize=200; ActiveTerrain->HeightAnchor=30000;
    ActiveTerrain->OceanMaxLod=16; ActiveTerrain->OceanLodResolution=64; ActiveTerrain->OceanTriangleSize=400;
    ActiveTerrain->NoiseIntensity=850000; ActiveTerrain->bProjectPosition=false; ActiveTerrain->bGenerateCollision=false; ActiveTerrain->bGenerateCollisionInEditor=false;
    ActiveTerrain->Foliages.Empty(); ActiveTerrain->DistanceToFreezeGeneration=ActiveTerrain->PlanetScale*100;
    ActiveNoise=NewObject<USolarTerrainNoise>(ActiveTerrain); ActiveNoise->BodyIndex=FocusIndex; ActiveTerrain->WorldScapeNoise=ActiveNoise;
    if(TerrainMaterials.IsValidIndex(FocusIndex))
    {
        TerrainMID=UMaterialInstanceDynamic::Create(TerrainMaterials[FocusIndex],this);
        TerrainMID->SetScalarParameterValue(TEXT("Visibility"),0);
        ActiveTerrain->TerrainMaterial.DefaultMaterial=TerrainMID;
    }
    if(OceanMaterial)
    {
        OceanMID=UMaterialInstanceDynamic::Create(OceanMaterial,this);
        OceanMID->SetScalarParameterValue(TEXT("Visibility"),0);
        ActiveTerrain->OceanMaterial.DefaultMaterial=OceanMID;
    }
    UGameplayStatics::FinishSpawningActor(ActiveTerrain,Transform);
    bSurfaceMode=true;
}

void ASolarSystemActor::ConfigureAtmosphere()
{
    if(AtmosphereFocus==FocusIndex)return;
    AtmosphereFocus=FocusIndex;
    const auto& B=Bodies[FocusIndex];
    const bool Venus=FocusIndex==2,Earth=FocusIndex==3,Mars=FocusIndex==5,Giant=FocusIndex>=6;
    // Keep the opaque atmospheric ground below dry valleys and ocean triangle
    // interiors, which lie below the sphere's vertex radius (chord sagitta).
    // Keep the atmosphere's virtual ground below the navigable seabed. The
    // exponential scale compensation below preserves sea-level air density.
    const double Depression=(Venus||Mars||Earth)?12.:Giant?50.:0.;
    const float Hr=Venus?15.f:Mars?11.1f:Giant?45.f:8.f;
    const float Hm=Venus?12.f:Mars?8.f:Giant?20.f:1.2f;
    LocalAtmosphere->SetBottomRadius(B.RadiusKm-Depression);
    LocalAtmosphere->SetAtmosphereHeight(FMath::Max(1.,B.AtmosphereKm+Depression));
    LocalAtmosphere->SetRayleighExponentialDistribution(Hr);
    LocalAtmosphere->SetMieExponentialDistribution(Hm);
    LocalAtmosphere->SetRayleighScattering(Earth?FLinearColor(.005802,.013558,.0331):Mars?FLinearColor(.00004,.00007,.00015):Venus?FLinearColor(.008,.009,.01):FLinearColor(.00035,.0008,.0013));
    LocalAtmosphere->SetRayleighScatteringScale(FMath::Exp(Depression/Hr));
    LocalAtmosphere->SetMieScattering(Mars?FLinearColor(1,.57,.29):Venus?FLinearColor(1,.87,.61):FLinearColor::White);
    LocalAtmosphere->SetMieScatteringScale((Venus?.035:Mars?.005:Giant?.0008:.003996)*FMath::Exp(Depression/Hm));
    LocalAtmosphere->SetMieAbsorptionScale((Venus?.008:Mars?.0005:Giant?.0001:.000444)*FMath::Exp(Depression/Hm));
    LocalAtmosphere->SetMieAnisotropy(Mars?.65:Venus?.75:.8);
    LocalAtmosphere->SetOtherAbsorptionScale(Earth?.001881:0);
    LocalAtmosphere->SetMultiScatteringFactor(Venus?2:1);
    LocalAtmosphere->SetSkyAndAerialPerspectiveLuminanceFactor(Venus?FLinearColor(1.f,.72f,.40f):FLinearColor::White);
    LocalAtmosphere->SetGroundAlbedo(Venus?FColor(130,100,65):Mars?FColor(120,65,35):FColor(90,100,95));
    LocalAtmosphere->TraceSampleCountScale=2;
    LocalAtmosphere->SetVisibility(B.AtmosphereKm>0);
    VolumeClouds->SetVisibility((Earth||Venus)&&VolumeCloudMID!=nullptr);
    if(VolumeCloudMID)
    {
        VolumeCloudMID->SetScalarParameterValue(TEXT("BodyIndex"),FocusIndex);
        VolumeCloudMID->SetScalarParameterValue(TEXT("RadiusKm"),B.RadiusKm);
        VolumeCloudMID->SetScalarParameterValue(TEXT("CloudBottomKm"),Venus?48.:2.);
        VolumeCloudMID->SetScalarParameterValue(TEXT("CloudThicknessKm"),Venus?22.:7.);
        VolumeClouds->SetPlanetRadius(B.RadiusKm-Depression);
        VolumeClouds->SetLayerBottomAltitude((Venus?48.:2.)+Depression);
        VolumeClouds->SetLayerHeight(Venus?22.:7.);
        VolumeClouds->SetTracingStartMaxDistance(50000);
        VolumeClouds->SetTracingMaxDistance(1800);
        // Direct per-pixel rendering avoids VRT reconstruction and half-float depth rejection.
        // Spend rays on every pixel while bounding depth samples (96 * .25 = 24).
        VolumeClouds->SetViewSampleCountScale(.25);
        VolumeClouds->SetShadowViewSampleCountScale(.25);
        VolumeClouds->SetbUsePerSampleAtmosphericLightTransmittance(true);
    }
}

void ASolarSystemActor::UpdateTerrain(float Dt,const FVector& CameraPosition)
{
    const double Alt=CameraPosition.Size()/SolarModel::CmPerKm-Bodies[FocusIndex].RadiusKm;
    if(Bodies[FocusIndex].bSolid&&Alt<1800)EnsureTerrain();
    if(!ActiveTerrain)return;
    TerrainWarmup+=Dt;
    bool Ready=ActiveTerrain->WorldScapeLod.Num()==16;
    for(const auto& L:ActiveTerrain->WorldScapeLod)Ready &= L&&L->Mesh&&L->Mesh->GetNumSections()>0;
    const float Target=(Ready&&TerrainWarmup>1)?1-FMath::SmoothStep(180.,450.,Alt):0;
    TerrainBlend=FMath::FInterpConstantTo(TerrainBlend,Target,Dt,.7f);
    if(TerrainMID)TerrainMID->SetScalarParameterValue(TEXT("Visibility"),TerrainBlend);
    if(OceanMID)OceanMID->SetScalarParameterValue(TEXT("Visibility"),TerrainBlend);
    // All near-water pixels have faded by 20 km. Remove the fully faded meshes
    // from the separate water pass too; its composite can retain clipmap edges.
    for(const auto& L:ActiveTerrain->WorldScapeLodOcean)
        if(L&&L->Mesh)L->Mesh->SetHiddenInGame(Alt>=20.);
    if(Alt>2400&&TerrainBlend==0)ClearTerrain();
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
        if(H<.015)continue;
        auto Region=SolarModel::SurfaceRegion(3,D,H);
        if(Region.Vegetation<.05)continue;
        const double Slope=SolarModel::SurfaceSlope(3,D,Bodies[3].RadiusKm);
        Region=SolarModel::SurfaceRegion(3,D,H,Slope);
        if(Region.Snow>.15||Region.Sand>.5||Slope>.14)continue;
        const double Density=Region.Vegetation*(I<700?FMath::Clamp((Region.Moisture-.35)/.35,0.,1.):1.);
        if(Random.FRand()>Density)continue;
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
    const FVector Logical=GetLogicalPositionKm();
    const double CurrentDistance=(Logical-Positions[FocusIndex]).Size();
    for(int I=1;I<Bodies.Num();++I)if(I!=FocusIndex)
    {
        const double Distance=(Logical-Positions[I]).Size();
        if(Distance<Bodies[I].RadiusKm*12 && Distance<CurrentDistance*.65){ReframeBody(I);break;}
    }
    const double Alt=P->GetActorLocation().Size()/SolarModel::CmPerKm-Bodies[FocusIndex].RadiusKm;
    // Streaming changes render detail only; never changes the camera pose or speed.
    UpdateTerrain(Dt,P->GetActorLocation());
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
    ConfigureAtmosphere();
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
        // The ocean proxy has its own 5-20 km coverage transition, including
        // while the land clipmap is fully active. Its land pixels still mask out.
        Spheres[I]->SetVisibility(!(I==FocusIndex&&TerrainBlend>=1&&!Bodies[I].bOcean));
        const FVector SunLocal=I==0?FVector::UpVector:Rotations[I].UnrotateVector(-Positions[I]).GetSafeNormal();
        if(SurfaceMIDs[I])
        {
            SurfaceMIDs[I]->SetVectorParameterValue(TEXT("SunDirection"),FLinearColor(SunLocal.X,SunLocal.Y,SunLocal.Z));
            SurfaceMIDs[I]->SetScalarParameterValue(TEXT("Visibility"),I==FocusIndex?1-TerrainBlend:1);
            SurfaceMIDs[I]->SetScalarParameterValue(TEXT("DisplayScale"),Scale);
            SurfaceMIDs[I]->SetScalarParameterValue(TEXT("VenusCloudCover"),I==2&&I!=FocusIndex?1:0);
            SurfaceMIDs[I]->SetScalarParameterValue(TEXT("ActiveBody"),I==FocusIndex?1:0);
            const double BodyAU=FMath::Max(.2,Positions[I].Size()/SolarModel::AU);
            SurfaceMIDs[I]->SetScalarParameterValue(TEXT("SolarIlluminance"),SolarIlluminanceAtOneAU/FMath::Square(BodyAU));
        }
        Shells[I]->SetWorldLocationAndRotation(Center,Q); Shells[I]->SetWorldScale3D(FVector((R+Bodies[I].AtmosphereKm*SolarModel::CmPerKm*Scale)/50));
        Shells[I]->SetVisibility(Bodies[I].AtmosphereKm>0 && I!=FocusIndex);
        const double VisualAU=FMath::Max(.2,Positions[I].Size()/SolarModel::AU);
        const float VisualLux=SolarIlluminanceAtOneAU/FMath::Square(VisualAU);
        if(ShellMIDs[I]) { ShellMIDs[I]->SetVectorParameterValue(TEXT("SunDirection"),FLinearColor(SunLocal.X,SunLocal.Y,SunLocal.Z)); ShellMIDs[I]->SetScalarParameterValue(TEXT("SolarIlluminance"),VisualLux); }
        if(I==3) { Clouds->SetWorldLocationAndRotation(Center,Q); Clouds->SetWorldScale3D(FVector((R+550000*Scale)/50)); Clouds->SetVisibility(I!=FocusIndex); if(CloudMID)CloudMID->SetVectorParameterValue(TEXT("SunDirection"),FLinearColor(SunLocal.X,SunLocal.Y,SunLocal.Z)); }
        if(PlanetRings.IsValidIndex(I)&&PlanetRings[I])
        {
            PlanetRings[I]->SetWorldLocationAndRotation(Center,Q);PlanetRings[I]->SetWorldScale3D(FVector(R));
            if(RingMIDs[I])
            {
                RingMIDs[I]->SetVectorParameterValue(TEXT("SunDirection"),FLinearColor(SunLocal.X,SunLocal.Y,SunLocal.Z));
                RingMIDs[I]->SetScalarParameterValue(TEXT("SolarIlluminance"),VisualLux);
                RingMIDs[I]->SetScalarParameterValue(TEXT("SunAngularRadius"),FMath::Atan(Bodies[0].RadiusKm/FMath::Max(1.,Positions[I].Size())));
            }
        }
        if(I==3&&CloudMID)CloudMID->SetScalarParameterValue(TEXT("SolarIlluminance"),VisualLux);
    }
    const FVector Light=GetFocusSunDirection(); SunLight->SetWorldRotation((-Light).Rotation());
    const double DistanceAU=FMath::Max(.2,Positions[FocusIndex].Size()/SolarModel::AU);
    SunLight->SetIntensity(FocusIndex==0?0:SolarIlluminanceAtOneAU/FMath::Square(DistanceAU));
    // ISO 100, f/16, 1/125 s: EV100 14.966. No histogram/eye adaptation.
    // A distance preset keeps outer-planet inspection usable without adapting when turning.
    LightingExposure->Settings.AutoExposureBias=ExposureCompensation+
        ((bCompensateExposureForSolarDistance&&FocusIndex!=0)?2*FMath::Log2(DistanceAU):0);
    const double AltitudeKm=ObserverLocalCm.Size()/SolarModel::CmPerKm-Bodies[FocusIndex].RadiusKm;
    const bool HasSurfaceSky=Bodies[FocusIndex].bSolid&&Bodies[FocusIndex].AtmosphereKm>0;
    const double SunElevation=FVector::DotProduct(ObserverLocalCm.GetSafeNormal(),Light);
    const float SkyStrength=HasSurfaceSky?
        (1-FMath::SmoothStep(20.,120.,AltitudeKm))*FMath::SmoothStep(-.12,.12,SunElevation):0;
    SurfaceSkyLight->SetWorldLocation(ObserverLocalCm);
    SurfaceSkyLight->SetIntensity(SkyStrength);
    SurfaceSkyLight->SetVisibility(SkyStrength>0);
    const FLinearColor LightVector(Light.X,Light.Y,Light.Z);
    if(TerrainMID)TerrainMID->SetVectorParameterValue(TEXT("SunDirection"),LightVector);
    if(OceanMID)OceanMID->SetVectorParameterValue(TEXT("SunDirection"),LightVector);
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
    Root->SetNumberField(TEXT("terrain_blend"),TerrainBlend);
    Root->SetBoolField(TEXT("volumetric_clouds"),VolumeClouds->IsVisible());
    if(const APawn* Pawn=UGameplayStatics::GetPlayerPawn(this,0))Root->SetNumberField(TEXT("earth_cloud_column"),GetCloudCoverage(Pawn->GetActorLocation()));
    Root->SetNumberField(TEXT("atmosphere_bottom_km"),LocalAtmosphere->BottomRadius);
    auto Regions=MakeShared<FJsonObject>();
    Regions->SetNumberField(TEXT("main_belt_inner_au"),SolarModel::MainBeltInnerAU);Regions->SetNumberField(TEXT("main_belt_outer_au"),SolarModel::MainBeltOuterAU);
    Regions->SetNumberField(TEXT("kuiper_inner_au"),SolarModel::KuiperBeltInnerAU);Regions->SetNumberField(TEXT("kuiper_outer_au"),SolarModel::KuiperBeltOuterAU);
    Root->SetObjectField(TEXT("reserved_regions"),Regions);
    TArray<TSharedPtr<FJsonValue>> Rows;
    for(int I=0;I<Bodies.Num();++I) { auto B=MakeShared<FJsonObject>();B->SetStringField(TEXT("key"),Bodies[I].Key);B->SetNumberField(TEXT("radius_km"),Bodies[I].RadiusKm); B->SetNumberField(TEXT("semi_major_axis_km"),Bodies[I].SemiMajorAxisKm);B->SetNumberField(TEXT("period_days"),Bodies[I].PeriodDays);B->SetBoolField(TEXT("tidal_lock"),Bodies[I].bTidalLock);B->SetNumberField(TEXT("atmosphere_km"),Bodies[I].AtmosphereKm);if(Positions.IsValidIndex(I))B->SetField(TEXT("position_km"),VectorJson(Positions[I]));Rows.Add(MakeShared<FJsonValueObject>(B)); }
    Root->SetArrayField(TEXT("bodies"),Rows);return JsonText(Root);
}

FString ASolarSystemActor::GetSurfaceRegion(int32 BodyIndex,FVector Direction,float Slope) const
{
    if(BodyIndex<1||BodyIndex>5)return TEXT("{\"error\":\"Body has no rocky surface\"}");
    const FVector N=Direction.GetSafeNormal(1e-12,FVector::UpVector);
    const double H=SolarModel::HeightKm(BodyIndex,N);
    const double ActualSlope=Slope<0?SolarModel::SurfaceSlope(BodyIndex,N,Bodies[BodyIndex].RadiusKm):FMath::Clamp(double(Slope),0.,1.);
    const auto R=SolarModel::SurfaceRegion(BodyIndex,N,H,ActualSlope);
    auto Row=MakeShared<FJsonObject>();
    Row->SetNumberField(TEXT("body"),BodyIndex);Row->SetNumberField(TEXT("height_km"),H);Row->SetNumberField(TEXT("slope"),ActualSlope);
    Row->SetNumberField(TEXT("sand"),R.Sand);Row->SetNumberField(TEXT("rock"),R.Rock);Row->SetNumberField(TEXT("soil"),R.Soil);Row->SetNumberField(TEXT("snow"),R.Snow);
    Row->SetNumberField(TEXT("temperature_index"),R.Temperature);Row->SetNumberField(TEXT("moisture_index"),R.Moisture);
    Row->SetNumberField(TEXT("vegetation"),R.Vegetation);Row->SetNumberField(TEXT("water"),R.Water);Row->SetField(TEXT("color"),VectorJson(R.Color));
    return JsonText(Row);
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
        const FVector EarthInMoon=Q[4].UnrotateVector((P[3]-P[4]).GetSafeNormal());
        Check(EarthInMoon.X>0&&FMath::Abs(EarthInMoon.Y)<1e-10,TEXT("Moon sub-Earth longitude must remain locked"));
        for(int I=0;I<Bodies.Num();++I)
        {
            const double Tilt=FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp(FVector::DotProduct(Q[I].GetUpVector(),SolarModel::OrbitNormal(Bodies[I])),-1.,1.)));
            Check(FMath::Abs(Tilt-Bodies[I].AxialTiltDeg)<1e-6,TEXT("Spin obliquity must be relative to the orbital plane"));
        }
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
    Check(Bodies[5].SemiMajorAxisKm*(1+Bodies[5].Eccentricity)<SolarModel::MainBeltInnerAU*SolarModel::AU,TEXT("Space between Mars and main asteroid belt"));
    Check(Bodies[6].SemiMajorAxisKm*(1-Bodies[6].Eccentricity)>SolarModel::MainBeltOuterAU*SolarModel::AU,TEXT("Space between main asteroid belt and Jupiter"));
    Check(SolarModel::KuiperBeltOuterAU*SolarModel::AU>Bodies[9].SemiMajorAxisKm*(1+Bodies[9].Eccentricity),TEXT("Kuiper belt extends beyond Neptune"));
    for(int I=6;I<10;++I)Check(Bodies[I].AtmosphereKm>0&&!Bodies[I].bSolid,TEXT("Giant planets have atmospheres and no solid surface"));
    TArray<TSharedPtr<FJsonValue>> Axes;
    for(const FSolarBody& B:Bodies)
    {
        auto Row=MakeShared<FJsonObject>();Row->SetStringField(TEXT("key"),B.Key);Row->SetNumberField(TEXT("obliquity_deg"),B.AxialTiltDeg);
        Row->SetNumberField(TEXT("inclination_deg"),B.InclinationDeg);Row->SetNumberField(TEXT("eccentricity"),B.Eccentricity);
        Row->SetNumberField(TEXT("radius_km"),B.RadiusKm);Row->SetNumberField(TEXT("semi_major_axis_au"),B.SemiMajorAxisKm/SolarModel::AU);
        Row->SetField(TEXT("spin_axis_ecliptic"),VectorJson(SolarModel::SpinAxis(B))); Axes.Add(MakeShared<FJsonValueObject>(Row));
    }
    Report->SetArrayField(TEXT("catalogue_audit"),Axes);
    Report->SetArrayField(TEXT("failures"),Failures);Report->SetBoolField(TEXT("success"),Failures.IsEmpty());Report->SetNumberField(TEXT("earth_water_fraction"),Water/512.);Report->SetNumberField(TEXT("terrain_invalid"),Invalid);return JsonText(Report);
}
