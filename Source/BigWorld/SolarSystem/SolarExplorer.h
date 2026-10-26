#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/HUD.h"
#include "SolarExplorer.generated.h"
class UCameraComponent;
class ASolarSystemActor;

UCLASS()
class BIGWORLD_API ASolarExplorerPawn : public APawn
{
    GENERATED_BODY()
public:
    ASolarExplorerPawn();
    virtual void Tick(float DeltaSeconds) override;
    UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="Camera") TObjectPtr<UCameraComponent> Camera;
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Flight") double SpeedKmPerSecond=100;
    UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="Flight") double EffectiveSpeedKmPerSecond=100;
    UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="Flight") bool bAutomaticSpeed=true;
    UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="Flight") double ManualSpeedKmPerSecond=100;
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Flight",meta=(ClampMin=".25",ClampMax="30")) double SpeedAdjustmentDoublingSeconds=4;
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Flight") bool bSurfaceHorizon=true;
    UFUNCTION(BlueprintCallable,Category="Flight") void SetViewPose(FVector Location,FRotator Rotation);
    // Also available to scripted camera paths; uses the same movement as keyboard input.
    UFUNCTION(BlueprintCallable,Category="Flight") void ApplyFlightInput(FVector Direction,double DeltaSeconds,bool bIncreaseSpeed,bool bDecreaseSpeed);
private:
    bool bSpeedResetChord=false;
    ASolarSystemActor* System() const;
};

UCLASS()
class BIGWORLD_API ASolarExplorerHUD : public AHUD
{
    GENERATED_BODY()
public:
    virtual void DrawHUD() override;
};

UCLASS()
class BIGWORLD_API ASolarExplorerGameMode : public AGameModeBase
{
    GENERATED_BODY()
public:
    ASolarExplorerGameMode();
};
