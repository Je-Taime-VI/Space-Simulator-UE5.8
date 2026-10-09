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
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Flight") bool bSurfaceHorizon=true;
    UFUNCTION(BlueprintCallable,Category="Flight") void SetViewPose(FVector Location,FRotator Rotation);
private:
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
