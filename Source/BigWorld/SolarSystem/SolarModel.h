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
    // Azimuth of the pole's tilt direction projected into this body's orbital plane.
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Rotation") double PoleLongitudeDeg = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Body") double AtmosphereKm = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Body") int32 ParentIndex = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Body") bool bSolid = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Body") bool bOcean = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Rotation") bool bTidalLock = false;
};

// Non-reflected sample shared by terrain, foliage and the shader rules adapter.
struct FSolarSurfaceRegion
{
    FVector Color;
    float Sand, Rock, Soil, Snow, Temperature, Moisture, Vegetation, Water;
};

namespace SolarModel
{
    constexpr double AU = 149597870.7;
    constexpr double CmPerKm = 100000.0;
    // Reserved heliocentric regions, in AU. These are populations, not solid walls.
    constexpr double MainBeltInnerAU = 2.1, MainBeltOuterAU = 3.3;
    constexpr double KuiperBeltInnerAU = 30.0, KuiperBeltOuterAU = 50.0;
    BIGWORLD_API TArray<FSolarBody> Defaults();
    BIGWORLD_API FVector OrbitPosition(const FSolarBody& Body, double Seconds);
    BIGWORLD_API FVector OrbitNormal(const FSolarBody& Body);
    BIGWORLD_API FVector SpinAxis(const FSolarBody& Body);
    BIGWORLD_API void Evaluate(const TArray<FSolarBody>& Bodies, double Seconds, TArray<FVector>& Positions, TArray<FQuat>& Rotations);
    BIGWORLD_API double HeightKm(int32 Body, const FVector& UnitDirection);
    BIGWORLD_API FLinearColor SurfaceColor(int32 Body, const FVector& UnitDirection);
    BIGWORLD_API FSolarSurfaceRegion SurfaceRegion(int32 Body, const FVector& UnitDirection, double HeightKm, double Slope=0);
    BIGWORLD_API double SurfaceSlope(int32 Body, const FVector& UnitDirection, double RadiusKm);
    BIGWORLD_API float CloudDensity(const FVector& UnitDirection);
}
