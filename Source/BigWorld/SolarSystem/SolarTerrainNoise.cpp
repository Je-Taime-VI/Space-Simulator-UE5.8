#include "SolarTerrainNoise.h"
#include "SolarModel.h"

FNoiseData USolarTerrainNoise::GetNoise(CustomNoise,const DVector& Position,const DVector&,double,double,double,bool,double,DVector&,FNoiseData,bool)
{
    const FVector N=Position.ToFVector().GetSafeNormal(1e-12,FVector::UpVector);
    FNoiseData D; D.Height=SolarModel::HeightKm(BodyIndex,N)*SolarModel::CmPerKm;
    D.HeightNormalize=FMath::Clamp(D.Height/850000.,0.,1.);
    const auto Region=SolarModel::SurfaceRegion(BodyIndex,N,D.Height/SolarModel::CmPerKm);
    D.Temperature=Region.Temperature; D.Humidity=Region.Moisture;
    D.WaterMask=Region.Water; D.FoliageMask=Region.Vegetation;
    return D;
}
FNoiseData USolarTerrainNoise::GetOceanNoise(CustomNoise,const DVector&,const DVector&,double,double,double,bool,double,DVector&,FNoiseData,bool)
{
    FNoiseData D; D.Height=0; D.Temperature=.5; D.Humidity=1; D.WaterMask=1; return D;
}
