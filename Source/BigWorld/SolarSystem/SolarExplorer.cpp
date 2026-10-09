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
    if(PC->WasInputKeyJustPressed(EKeys::G)) S->VisitSurface();
    if(PC->WasInputKeyJustPressed(EKeys::O)) S->FocusBody(S->FocusIndex);
    if(PC->WasInputKeyJustPressed(EKeys::P)) S->SetTimeScale(S->TimeScale==0?1:0);
    if(PC->WasInputKeyJustPressed(EKeys::Period)) S->SetTimeScale(FMath::Clamp(S->TimeScale==0?1:S->TimeScale*10,1.,100000.));
    if(PC->WasInputKeyJustPressed(EKeys::Comma)) S->SetTimeScale(FMath::Max(1.,S->TimeScale/10));
    if(PC->WasInputKeyJustPressed(EKeys::Home)) S->SetSimulationTime(0);
    if(PC->WasInputKeyJustPressed(EKeys::MouseScrollUp))SpeedKmPerSecond=FMath::Min(1e7,SpeedKmPerSecond*2);
    if(PC->WasInputKeyJustPressed(EKeys::MouseScrollDown))SpeedKmPerSecond=FMath::Max(.001,SpeedKmPerSecond/2);
    float MX=0,MY=0; PC->GetInputMouseDelta(MX,MY);
    FQuat Q=GetActorQuat(); const FVector Up=(S->bSurfaceMode&&bSurfaceHorizon)?GetActorLocation().GetSafeNormal():Q.GetUpVector();
    Q=FQuat(Up,FMath::DegreesToRadians(MX*.14))*Q;
    Q=FQuat(Q.GetRightVector(),FMath::DegreesToRadians(-MY*.14))*Q;
    if(S->bSurfaceMode&&bSurfaceHorizon && FMath::Abs(FVector::DotProduct(Q.GetForwardVector(),Up))<.99) Q=FRotationMatrix::MakeFromXZ(Q.GetForwardVector(),Up).ToQuat();
    SetActorRotation(Q);
    FVector Move=Q.GetForwardVector()*double(PC->IsInputKeyDown(EKeys::W)-PC->IsInputKeyDown(EKeys::S));
    Move+=Q.GetRightVector()*double(PC->IsInputKeyDown(EKeys::D)-PC->IsInputKeyDown(EKeys::A));
    Move+=Up*double((PC->IsInputKeyDown(EKeys::E)||PC->IsInputKeyDown(EKeys::SpaceBar))-(PC->IsInputKeyDown(EKeys::Q)||PC->IsInputKeyDown(EKeys::LeftControl)));
    if(!Move.IsNearlyZero())
    {
        FVector P=GetActorLocation()+Move.GetSafeNormal()*SpeedKmPerSecond*SolarModel::CmPerKm*Dt*(PC->IsInputKeyDown(EKeys::LeftShift)?10:1);
        const FVector N=P.GetSafeNormal(1e-12,Up);
        const double Minimum=(S->GetGroundRadiusKm(N)+.003)*SolarModel::CmPerKm;
        if(P.Size()<Minimum)P=N*Minimum;
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
    DrawText(FString::Printf(TEXT("%s  ·  %s"),*B.DisplayName,S->bSurfaceMode?TEXT("地表巡视"):TEXT("轨道巡视")),FLinearColor::White,X,Y+27,GEngine->GetMediumFont(),1.05);
    const double Alt=P->GetActorLocation().Size()/SolarModel::CmPerKm-B.RadiusKm;
    DrawText(FString::Printf(TEXT("半径 %.1f km    海拔 %.3f km"),B.RadiusKm,Alt),FLinearColor(.73,.79,.84),X,Y+59,GEngine->GetSmallFont());
    DrawText(FString::Printf(TEXT("速度 %.3g km/s    时间 ×%.0f    J2000 + %.2f 日"),P->SpeedKmPerSecond,S->TimeScale,S->SimulationSeconds/86400),FLinearColor(.73,.79,.84),X,Y+81,GEngine->GetSmallFont());
    const double Gravity=B.MuKm3S2/FMath::Square(FMath::Max(B.RadiusKm,P->GetActorLocation().Size()/SolarModel::CmPerKm))*1000;
    DrawText(FString::Printf(TEXT("当地引力 %.3f m/s²    %s"),Gravity,B.bTidalLock?TEXT("潮汐锁定 · 无大气"):B.bSolid?TEXT("岩质天体"):S->FocusIndex==0?TEXT("恒星光球"):TEXT("气体 / 冰巨星 · 无固体地表")),FLinearColor(.57,.68,.76),X,Y+105,GEngine->GetSmallFont());
    DrawRect(FLinearColor(.009,.017,.029,.84),14,Canvas->SizeY-67,Canvas->SizeX-28,53);
    DrawText(TEXT("0 太阳   1 水星   2 金星   3 地球   4 月球   5 火星   6 木星   7 土星   8 天王星   9 海王星"),FLinearColor(.78,.84,.9),26,Canvas->SizeY-61,GEngine->GetSmallFont());
    DrawText(TEXT("WASD 移动 · 鼠标转向 · Q/E 升降 · 滚轮速度 · Shift 加速 · G 地表 · O 轨道 · ,/. 时间倍率 · P 暂停 · Home 纪元"),FLinearColor(.50,.66,.74),26,Canvas->SizeY-38,GEngine->GetSmallFont());
}
