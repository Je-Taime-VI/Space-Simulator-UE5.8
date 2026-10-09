#include "SolarTerrainNoise.h"
#include "SolarModel.h"

FNoiseData USolarTerrainNoise::GetNoise(CustomNoise,const DVector& Position,const DVector&,double,double,double,bool,double,DVector&,FNoiseData,bool)
{
    const FVector N=Position.ToFVector().GetSafeNormal(1e-12,FVector::UpVector);
    FNoiseData D; D.Height=SolarModel::HeightKm(BodyIndex,N)*SolarModel::CmPerKm;
    D.HeightNormalize=FMath::Clamp(D.Height/850000.,0.,1.);
    D.Temperature=FMath::Clamp(1-FMath::Abs(N.Z)-FMath::Max(0.,D.Height)*.0000003,0.,1.);
    D.Humidity=.6; D.WaterMask=D.Height<0?1:0;
    D.FoliageMask=(BodyIndex==3 && D.Height>1000 && D.Height<220000 && FMath::Abs(N.Z)<.85)?1:0;
    return D;
}
FNoiseData USolarTerrainNoise::GetOceanNoise(CustomNoise,const DVector&,const DVector&,double,double,double,bool,double,DVector&,FNoiseData,bool)
{
    FNoiseData D; D.Height=0; D.Temperature=.5; D.Humidity=1; D.WaterMask=1; return D;
}
