#include "SolarExplorer.h"
#include "SolarSystemActor.h"
#include "Camera/CameraComponent.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "Components/SceneComponent.h"
#include "Math/RotationMatrix.h"
#include "InputCoreTypes.h"

namespace
{
double NavigationClearanceKm(const ASolarSystemActor* System,const FVector& Position)
{
    const FVector Up=Position.GetSafeNormal(1e-12,FVector::UpVector);
    double ReferenceRadius=System->GetGroundRadiusKm(Up);
    // Keep automatic approach speed conservative around the sea surface, while
    // movement collision below uses solid terrain and permits entering water.
    if(System->Bodies[System->FocusIndex].bOcean)
        ReferenceRadius=FMath::Max(ReferenceRadius,System->Bodies[System->FocusIndex].RadiusKm);
    return FMath::Max(.003,Position.Size()/SolarModel::CmPerKm-ReferenceRadius);
}
}

ASolarExplorerPawn::ASolarExplorerPawn()
{
    PrimaryActorTick.bCanEverTick=true;
    RootComponent=CreateDefaultSubobject<USceneComponent>(TEXT("Frame"));
    Camera=CreateDefaultSubobject<UCameraComponent>(TEXT("ExplorerCamera")); Camera->SetupAttachment(RootComponent);
    Camera->FieldOfView=60; Camera->bUsePawnControlRotation=false;
    AutoPossessPlayer=EAutoReceiveInput::Player0;
}
ASolarSystemActor* ASolarExplorerPawn::System() const { for(TActorIterator<ASolarSystemActor> It(GetWorld());It;++It)return *It; return nullptr; }
void ASolarExplorerPawn::SetViewPose(FVector P,FRotator R) { SetActorLocationAndRotation(P,R,false,nullptr,ETeleportType::TeleportPhysics); if(Controller)Controller->SetControlRotation(R); }
void ASolarExplorerPawn::Tick(float Dt)
{
    Super::Tick(Dt);
    auto* PC=Cast<APlayerController>(Controller); auto* S=System(); if(!PC||!S)return;
    const FKey Keys[]={EKeys::Zero,EKeys::One,EKeys::Two,EKeys::Three,EKeys::Four,EKeys::Five,EKeys::Six,EKeys::Seven,EKeys::Eight,EKeys::Nine};
    for(int I=0;I<10;++I)if(PC->WasInputKeyJustPressed(Keys[I]))S->FocusBody(I);
    if(PC->WasInputKeyJustPressed(EKeys::P)) S->SetTimeScale(S->TimeScale==0?1:0);
    if(PC->WasInputKeyJustPressed(EKeys::Period)) S->SetTimeScale(FMath::Clamp(S->TimeScale==0?1:S->TimeScale*10,1.,100000.));
    if(PC->WasInputKeyJustPressed(EKeys::Comma)) S->SetTimeScale(FMath::Max(1.,S->TimeScale/10));
    if(PC->WasInputKeyJustPressed(EKeys::Home)) S->SetSimulationTime(0);
    double& WheelSpeed=bAutomaticSpeed?SpeedKmPerSecond:ManualSpeedKmPerSecond;
    if(PC->WasInputKeyJustPressed(EKeys::MouseScrollUp))WheelSpeed=FMath::Min(1e7,WheelSpeed*1.2);
    if(PC->WasInputKeyJustPressed(EKeys::MouseScrollDown))WheelSpeed=FMath::Max(bAutomaticSpeed?.001:.00001,WheelSpeed/1.2);
    float MX=0,MY=0; PC->GetInputMouseDelta(MX,MY);
    FQuat Q=GetActorQuat();
    const FVector Radial=GetActorLocation().GetSafeNormal(1e-12,FVector::UpVector);
    const double Clearance=NavigationClearanceKm(S,GetActorLocation());
    const FVector Up=bSurfaceHorizon?Radial:Q.GetUpVector();
    Q=FQuat(Up,FMath::DegreesToRadians(MX*.14))*Q;
    Q=FQuat(Q.GetRightVector(),FMath::DegreesToRadians(-MY*.14))*Q;
    // Roll assistance changes smoothly and only while steering; streaming cannot reset it.
    if(bSurfaceHorizon && Clearance<50 && (FMath::Abs(MX)+FMath::Abs(MY)>.001) && FMath::Abs(FVector::DotProduct(Q.GetForwardVector(),Up))<.97)
        Q=FQuat::Slerp(Q,FRotationMatrix::MakeFromXZ(Q.GetForwardVector(),Up).ToQuat(),FMath::Clamp(Dt*3,0.,1.));
    SetActorRotation(Q);
    FVector Move=Q.GetForwardVector()*double(PC->IsInputKeyDown(EKeys::W)-PC->IsInputKeyDown(EKeys::S));
    Move+=Q.GetRightVector()*double(PC->IsInputKeyDown(EKeys::D)-PC->IsInputKeyDown(EKeys::A));
    Move+=Up*double((PC->IsInputKeyDown(EKeys::E)||PC->IsInputKeyDown(EKeys::SpaceBar))-PC->IsInputKeyDown(EKeys::Q));
    ApplyFlightInput(Move,Dt,PC->IsInputKeyDown(EKeys::LeftShift),PC->IsInputKeyDown(EKeys::LeftControl));
}

void ASolarExplorerPawn::ApplyFlightInput(FVector Direction,double DeltaSeconds,bool bIncreaseSpeed,bool bDecreaseSpeed)
{
    const auto* S=System(); if(!S)return;
    const FVector Up=GetActorLocation().GetSafeNormal(1e-12,FVector::UpVector);
    const double Clearance=NavigationClearanceKm(S,GetActorLocation());
    const double BaseSpeed=FMath::Max(.001,SpeedKmPerSecond);
    const double AutomaticSpeed=FMath::Min(BaseSpeed,FMath::Max(.01,Clearance*.35));
    if(bIncreaseSpeed&&bDecreaseSpeed)
    {
        bAutomaticSpeed=true;
        bSpeedResetChord=true;
    }
    else if(bSpeedResetChord)
    {
        // Releasing the reset chord one key at a time must not re-enter manual mode.
        if(!bIncreaseSpeed&&!bDecreaseSpeed)bSpeedResetChord=false;
    }
    else if(bIncreaseSpeed||bDecreaseSpeed)
    {
        // Start from the speed at this altitude, with no jump to the orbital setting.
        if(bAutomaticSpeed)ManualSpeedKmPerSecond=AutomaticSpeed;
        bAutomaticSpeed=false;
        const double Exponent=(bIncreaseSpeed?1.:-1.)*FMath::Clamp(DeltaSeconds,0.,.1)/FMath::Clamp(SpeedAdjustmentDoublingSeconds,.25,30.);
        ManualSpeedKmPerSecond=FMath::Clamp(ManualSpeedKmPerSecond*FMath::Pow(2.,Exponent),.00001,1e7);
    }
    EffectiveSpeedKmPerSecond=bAutomaticSpeed?AutomaticSpeed:ManualSpeedKmPerSecond;
    if(!Direction.IsNearlyZero())
    {
        // Retained manual speed bypasses both proximity caps, even after key release.
        // Radial clearance remains a camera aid, not swept collision.
        double StepKm=EffectiveSpeedKmPerSecond*FMath::Clamp(DeltaSeconds,0.,.1);
        if(bAutomaticSpeed)StepKm=FMath::Min(StepKm,FMath::Max(.001,Clearance*.4));
        const int Steps=FMath::Clamp(FMath::CeilToInt(FMath::Min(32.,StepKm/.1)),1,32);
        const FVector Step=Direction.GetSafeNormal()*StepKm*SolarModel::CmPerKm/Steps;
        FVector P=GetActorLocation();
        for(int I=0;I<Steps;++I)
        {
            P+=Step;
            const FVector N=P.GetSafeNormal(1e-12,Up);
            const double Minimum=(S->GetGroundRadiusKm(N)+.003)*SolarModel::CmPerKm;
            if(P.Size()<Minimum)P=N*Minimum;
        }
        SetActorLocation(P,false,nullptr,ETeleportType::TeleportPhysics);
    }
}

ASolarExplorerGameMode::ASolarExplorerGameMode() { DefaultPawnClass=ASolarExplorerPawn::StaticClass(); HUDClass=ASolarExplorerHUD::StaticClass(); }

void ASolarExplorerHUD::DrawHUD()
{
    Super::DrawHUD(); if(!Canvas)return;
    ASolarSystemActor* S=nullptr; for(TActorIterator<ASolarSystemActor> It(GetWorld());It;++It){S=*It;break;}
    if(!S||!S->Bodies.IsValidIndex(S->FocusIndex))return;
    auto* P=Cast<ASolarExplorerPawn>(GetOwningPawn()); if(!P)return;
    const FSolarBody& B=S->Bodies[S->FocusIndex];
    const float X=26,Y=24,W=450;
    DrawRect(FLinearColor(.009,.017,.029,.88),X-12,Y-10,W,146);
    DrawText(TEXT("SOLAR SYSTEM  /  真实尺度探索"),FLinearColor(.39,.81,.95),X,Y,GEngine->GetMediumFont(),.95);
    DrawText(FString::Printf(TEXT("%s  ·  连续飞行"),*B.DisplayName),FLinearColor::White,X,Y+27,GEngine->GetMediumFont(),1.05);
    const double Alt=P->GetActorLocation().Size()/SolarModel::CmPerKm-B.RadiusKm;
    const TCHAR* AltLabel=S->FocusIndex>=6?TEXT("距1 bar参考层"):TEXT("海拔");
    DrawText(FString::Printf(TEXT("半径 %.1f km    %s %.3f km"),B.RadiusKm,AltLabel,Alt),FLinearColor(.73,.79,.84),X,Y+59,GEngine->GetSmallFont());
    const bool bMetres=P->EffectiveSpeedKmPerSecond<1;
    DrawText(FString::Printf(TEXT("速度 %.3g %s · %s    时间 ×%.0f    J2000 + %.2f 日"),P->EffectiveSpeedKmPerSecond*(bMetres?1000:1),bMetres?TEXT("m/s"):TEXT("km/s"),P->bAutomaticSpeed?TEXT("自动"):TEXT("手动"),S->TimeScale,S->SimulationSeconds/86400),FLinearColor(.73,.79,.84),X,Y+81,GEngine->GetSmallFont());
    const double Gravity=B.MuKm3S2/FMath::Square(FMath::Max(B.RadiusKm,P->GetActorLocation().Size()/SolarModel::CmPerKm))*1000;
    DrawText(FString::Printf(TEXT("当地引力 %.3f m/s²    %s"),Gravity,B.bTidalLock?TEXT("潮汐锁定 · 无大气"):B.bSolid?TEXT("岩质天体"):S->FocusIndex==0?TEXT("恒星光球"):TEXT("气体 / 冰巨星 · 无固体地表")),FLinearColor(.57,.68,.76),X,Y+105,GEngine->GetSmallFont());
    DrawRect(FLinearColor(.009,.017,.029,.84),14,Canvas->SizeY-67,Canvas->SizeX-28,53);
    DrawText(TEXT("0 太阳   1 水星   2 金星   3 地球   4 月球   5 火星   6 木星   7 土星   8 天王星   9 海王星"),FLinearColor(.78,.84,.9),26,Canvas->SizeY-61,GEngine->GetSmallFont());
    DrawText(TEXT("WASD 飞行 · Q/E 升降 · 左Shift/Ctrl 调速，松开保持，同按自动 · 滚轮微调 · 数字键天体 · ,/. 时间 · P 暂停"),FLinearColor(.50,.66,.74),26,Canvas->SizeY-38,GEngine->GetSmallFont());
}
