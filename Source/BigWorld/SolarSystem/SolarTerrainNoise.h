#pragma once
#include "CoreMinimal.h"
#include "WorldScapeNoiseClass.h"
#include "SolarTerrainNoise.generated.h"

UCLASS(BlueprintType)
class BIGWORLD_API USolarTerrainNoise : public UWorldScapeNoiseClass
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Solar") int32 BodyIndex=3;
    virtual FNoiseData GetNoise(CustomNoise NoiseClass,const DVector& Position,const DVector& PlanetPosition,double NoiseScale,double NoiseIntensity,double PlanetScale,bool FlatWorld,double Latitude,DVector& NoisePosition,FNoiseData ActualData,bool UsePlanetary) override;
    virtual FNoiseData GetOceanNoise(CustomNoise NoiseClass,const DVector& Position,const DVector& PlanetPosition,double NoiseScale,double NoiseIntensity,double PlanetScale,bool FlatWorld,double Latitude,DVector& NoisePosition,FNoiseData ActualData,bool UsePlanetary) override;
};
