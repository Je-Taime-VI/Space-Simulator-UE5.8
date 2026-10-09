#pragma once
#include "CoreMinimal.h"
#include "SolarModel.generated.h"

USTRUCT(BlueprintType)
struct BIGWORLD_API FSolarBody
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Body") FString Key;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Body") FString DisplayName;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Body") double RadiusKm = 1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Body") double MuKm3S2 = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Orbit") double SemiMajorAxisKm = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Orbit") double Eccentricity = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Orbit") double InclinationDeg = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Orbit") double AscendingNodeDeg = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Orbit") double PeriapsisDeg = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Orbit") double MeanAnomalyDeg = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Orbit") double PeriodDays = 1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Rotation") double SpinDays = 1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Rotation") double AxialTiltDeg = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Body") double AtmosphereKm = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Body") int32 ParentIndex = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Body") bool bSolid = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Body") bool bOcean = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Rotation") bool bTidalLock = false;
};

namespace SolarModel
{
    constexpr double AU = 149597870.7;
    constexpr double CmPerKm = 100000.0;
    BIGWORLD_API TArray<FSolarBody> Defaults();
    BIGWORLD_API FVector OrbitPosition(const FSolarBody& Body, double Seconds);
    BIGWORLD_API void Evaluate(const TArray<FSolarBody>& Bodies, double Seconds, TArray<FVector>& Positions, TArray<FQuat>& Rotations);
    BIGWORLD_API double HeightKm(int32 Body, const FVector& UnitDirection);
    BIGWORLD_API FLinearColor SurfaceColor(int32 Body, const FVector& UnitDirection);
    BIGWORLD_API float CloudDensity(const FVector& UnitDirection);
}
