#include "SolarModel.h"
#include "Math/RotationMatrix.h"

namespace
{
double Noise(const FVector& P, int Octaves=5)
{
    double Value=0, Amp=0.5;
    FVector V=P;
    for (int I=0; I<Octaves; ++I) { Value += Amp*FMath::PerlinNoise3D(V); V=V*2.03+FVector(7.1,3.7,9.2); Amp*=0.5; }
    return Value;
}
double Smooth(double A,double B,double V) { const double T=FMath::Clamp((V-A)/(B-A),0.,1.); return T*T*(3-2*T); }
double Land(const FVector& N)
{
    const FVector Warp(Noise(N*2+FVector(12,4,0),3),Noise(N*2+FVector(2,17,3),3),Noise(N*2+FVector(8,7,19),3));
    return Noise(N*2.6+Warp*1.7+FVector(11.2,7.7,5.1),6)-0.06;
}
struct FRegionRules
{
    using float3=FVector;
    static float axisZ(const FVector& N) { return N.Z; }
    static float noise(const FVector& N,int Count) { return Noise(N,Count); }
    static float smoothstep(float A,float B,float V) { return Smooth(A,B,V); }
    static float saturate(float V) { return FMath::Clamp(V,0.f,1.f); }
    static float abs(float V) { return FMath::Abs(V); }
    static float pow(float A,float B) { return FMath::Pow(A,B); }
    static float exp(float V) { return FMath::Exp(V); }
    static float max(float A,float B) { return FMath::Max(A,B); }
    static float lerp(float A,float B,float T) { return FMath::Lerp(A,B,T); }
    static FVector lerp(const FVector& A,const FVector& B,float T) { return FMath::Lerp(A,B,T); }
    #include "SolarBiomeRules.inl"
};
double Craters(const FVector& N)
{
    // Cellular craters in 3D avoid a longitude seam and polar UV distortion.
    double H=0;
    for(int Layer=0;Layer<3;++Layer)
    {
        const double Scale=FMath::Pow(3.,Layer)*19.; const FVector P=N*Scale;
        const FIntVector Cell(FMath::FloorToInt(P.X),FMath::FloorToInt(P.Y),FMath::FloorToInt(P.Z));
        double Best=100;
        for(int X=-1;X<=1;++X) for(int Y=-1;Y<=1;++Y) for(int Z=-1;Z<=1;++Z)
        {
            const FIntVector C=Cell+FIntVector(X,Y,Z);
            uint32 Hash=uint32(C.X)*73856093u ^ uint32(C.Y)*19349663u ^ uint32(C.Z)*83492791u;
            auto R=[&Hash](){ Hash=Hash*1664525u+1013904223u; return double(Hash&65535)/65535.; };
            const double Rx=R(),Ry=R(),Rz=R();
            const FVector Center=FVector(C)+FVector(Rx,Ry,Rz);
            Best=FMath::Min(Best,FVector::Dist(P,Center));
        }
        const double Bowl=-FMath::Max(0.,1-FMath::Square(Best/0.39));
        const double Rim=0.23*FMath::Exp(-FMath::Square((Best-0.43)/0.065));
        H+=(Bowl+Rim)*1.8/FMath::Pow(3.,Layer);
    }
    return H;
}
}

TArray<FSolarBody> SolarModel::Defaults()
{
    TArray<FSolarBody> Result;
    auto Add=[&](const TCHAR* Key,const TCHAR* Name,double R,double Mu,double A,double E,double Inc,double Node,double LongPeri,double L,double Spin,double Tilt,double Atmo,bool Solid)
    {
        FSolarBody B; B.Key=Key; B.DisplayName=Name; B.RadiusKm=R; B.MuKm3S2=Mu; B.SemiMajorAxisKm=A*AU;
        B.Eccentricity=E; B.InclinationDeg=Inc; B.AscendingNodeDeg=Node; B.PeriapsisDeg=LongPeri-Node; B.MeanAnomalyDeg=L-LongPeri;
        B.PeriodDays=A>0 ? 2*PI*FMath::Sqrt(FMath::Pow(B.SemiMajorAxisKm,3)/(1.32712440018e11+Mu))/86400 : 1;
        B.SpinDays=Spin; B.AxialTiltDeg=Tilt; B.AtmosphereKm=Atmo; B.bSolid=Solid; Result.Add(B);
    };
    // JPL mean radii and J2000 elements. Fixed two-body orbits, not a precision ephemeris.
    Add(TEXT("Sun"),TEXT("太阳"),695700,1.32712440018e11,0,0,0,0,0,0,25.38,7.25,0,false);
    Add(TEXT("Mercury"),TEXT("水星"),2439.4,22031.86855,.38709927,.20563593,7.00497902,48.33076593,77.45779628,252.25032350,58.6462,.034,0,true);
    Add(TEXT("Venus"),TEXT("金星"),6051.8,324858.592,.72333566,.00677672,3.39467605,76.67984255,131.60246718,181.97909950,243.018,177.36,150,true);
    Add(TEXT("Earth"),TEXT("地球"),6371.0084,398600.435507,1.00000261,.01671123,-.00001531,0,102.93768193,100.46457166,.99726968,23.43928,100,true);
    Result.Last().bOcean=true;
    Add(TEXT("Moon"),TEXT("月球"),1737.4,4902.800118,384400/AU,.0549,5.145,125.08,318.15,218.316,27.321661,6.68,0,true);
    Result.Last().ParentIndex=3; Result.Last().PeriodDays=27.321661; Result.Last().bTidalLock=true;
    Add(TEXT("Mars"),TEXT("火星"),3389.5,42828.375816,1.52371034,.09339410,1.84969142,49.55953891,-23.94362959,-4.55343205,1.02595676,25.19,80,true);
    Add(TEXT("Jupiter"),TEXT("木星"),69911,126712764.1,5.202887,.04838624,1.30439695,100.47390909,14.72847983,34.39644051,.41354,3.13,300,false);
    Add(TEXT("Saturn"),TEXT("土星"),58232,37940584.84,9.53667594,.05386179,2.48599187,113.66242448,92.59887831,49.95424423,.44401,26.73,600,false);
    Add(TEXT("Uranus"),TEXT("天王星"),25362,5794556.4,19.18916464,.04725744,.77263783,74.01692503,170.95427630,313.23810451,.71833,97.77,350,false);
    Add(TEXT("Neptune"),TEXT("海王星"),24622,6836527.1,30.06992276,.00859048,1.77004347,131.78422574,44.96476227,-55.12002969,.67125,28.32,300,false);
    // IAU/NAIF J2000 pole directions converted from equatorial to ecliptic.
    // Preserve catalogue obliquity exactly; precession/nutation remain out of scope.
    const double RA[]={286.13,281.0103,272.76,0,269.9949,317.269202,268.056595,40.589,257.311,299.36};
    const double Dec[]={63.87,61.4155,67.16,90,66.5392,54.432516,64.495303,83.537,-15.175,43.46};
    const double Eps=FMath::DegreesToRadians(23.43928);
    for(int I=0;I<Result.Num();++I)
    {
        const double A=FMath::DegreesToRadians(RA[I]),D=FMath::DegreesToRadians(Dec[I]);
        FVector Pole(FMath::Cos(D)*FMath::Cos(A),FMath::Cos(Eps)*FMath::Cos(D)*FMath::Sin(A)+FMath::Sin(Eps)*FMath::Sin(D),-FMath::Sin(Eps)*FMath::Cos(D)*FMath::Sin(A)+FMath::Cos(Eps)*FMath::Sin(D));
        // IAU cartographic north uses a negative spin rate for these two bodies.
        // This model uses positive periods about the angular-momentum pole instead.
        if(I==2||I==8)Pole=-Pole;
        const FVector Normal=OrbitNormal(Result[I]);
        const FVector Tangent=(Pole-Normal*FVector::DotProduct(Pole,Normal)).GetSafeNormal();
        Result[I].PoleLongitudeDeg=FMath::RadiansToDegrees(FMath::Atan2(Tangent.Y,Tangent.X));
    }
    return Result;
}

FVector SolarModel::OrbitPosition(const FSolarBody& B,double Seconds)
{
    if(B.SemiMajorAxisKm<=0) return FVector::ZeroVector;
    const double M=FMath::UnwindRadians(FMath::DegreesToRadians(B.MeanAnomalyDeg)+2*PI*FMath::Fmod(Seconds/(B.PeriodDays*86400),1.));
    double E=M;
    for(int I=0;I<20;++I) { const double D=(E-B.Eccentricity*FMath::Sin(E)-M)/(1-B.Eccentricity*FMath::Cos(E)); E-=D; if(FMath::Abs(D)<1e-13)break; }
    const double X=B.SemiMajorAxisKm*(FMath::Cos(E)-B.Eccentricity);
    const double Y=B.SemiMajorAxisKm*FMath::Sqrt(1-B.Eccentricity*B.Eccentricity)*FMath::Sin(E);
    const double O=FMath::DegreesToRadians(B.AscendingNodeDeg), W=FMath::DegreesToRadians(B.PeriapsisDeg), I=FMath::DegreesToRadians(B.InclinationDeg);
    const double co=FMath::Cos(O),so=FMath::Sin(O),cw=FMath::Cos(W),sw=FMath::Sin(W),ci=FMath::Cos(I),si=FMath::Sin(I);
    return FVector((co*cw-so*sw*ci)*X+(-co*sw-so*cw*ci)*Y,(so*cw+co*sw*ci)*X+(-so*sw+co*cw*ci)*Y,sw*si*X+cw*si*Y);
}

FVector SolarModel::OrbitNormal(const FSolarBody& B)
{
    const double I=FMath::DegreesToRadians(B.InclinationDeg),O=FMath::DegreesToRadians(B.AscendingNodeDeg);
    return FVector(FMath::Sin(I)*FMath::Sin(O),-FMath::Sin(I)*FMath::Cos(O),FMath::Cos(I));
}
FVector SolarModel::SpinAxis(const FSolarBody& B)
{
    const FVector Normal=OrbitNormal(B);
    const double A=FMath::DegreesToRadians(B.PoleLongitudeDeg),T=FMath::DegreesToRadians(B.AxialTiltDeg);
    const double X=FMath::Cos(A),Y=FMath::Sin(A);
    const FVector Tangent=FVector(X,Y,-(Normal.X*X+Normal.Y*Y)/Normal.Z).GetSafeNormal();
    return (Normal*FMath::Cos(T)+Tangent*FMath::Sin(T)).GetSafeNormal();
}
void SolarModel::Evaluate(const TArray<FSolarBody>& Bodies,double Seconds,TArray<FVector>& P,TArray<FQuat>& Q)
{
    P.SetNum(Bodies.Num()); Q.SetNum(Bodies.Num());
    for(int I=0;I<Bodies.Num();++I) { P[I]=OrbitPosition(Bodies[I],Seconds); if(Bodies[I].ParentIndex>0)P[I]+=P[Bodies[I].ParentIndex]; }
    // Earth elements describe the Earth-Moon barycentre.
    if(Bodies.Num()>4) { const FVector Correction=(P[4]-P[3])*(Bodies[4].MuKm3S2/(Bodies[3].MuKm3S2+Bodies[4].MuKm3S2)); P[3]-=Correction; P[4]-=Correction; }
    for(int I=0;I<Bodies.Num();++I)
    {
        const auto& B=Bodies[I];
        if(B.bTidalLock)
        {
            const FVector Axis=SpinAxis(B),ToParent=(P[B.ParentIndex]-P[I]).GetSafeNormal();
            // Keep the sub-parent longitude fixed while retaining the oblique pole.
            Q[I]=FRotationMatrix::MakeFromXZ((ToParent-Axis*FVector::DotProduct(ToParent,Axis)).GetSafeNormal(),Axis).ToQuat();
        }
        else Q[I]=FRotationMatrix::MakeFromZ(SpinAxis(B)).ToQuat()*FQuat(FVector::UpVector,2*PI*FMath::Fmod(Seconds/(B.SpinDays*86400),1.));
    }
}

double SolarModel::HeightKm(int32 Body,const FVector& Direction)
{
    const FVector N=Direction.GetSafeNormal(1e-12,FVector::UpVector);
    if(Body==3)
    {
        const double C=Land(N), Hills=Noise(N*170+FVector(5,1,3),5), Ridge=1-FMath::Abs(Noise(N*32,5)*2);
        const double Mountains=Smooth(.03,.24,C)*FMath::Pow(FMath::Max(0.,Ridge),5)*3.8;
        // Kilometre-scale hills retain visible relief when visiting a full-size planet.
        const double LocalHills=Noise(N*9000+FVector(19,2,8),4)*.11;
        double H=C*18+Mountains+(Hills*.18+LocalHills)*Smooth(-.03,.08,C);
        if(FMath::Abs(N.Z)>.962) H=FMath::Max(H,0.08+(FMath::Abs(N.Z)-.962)*12+Hills*.1);
        return FMath::Clamp(H,-10.,8.5);
    }
    if(Body==4 || Body==1) return Noise(N*7+FVector(Body,9,3),5)*2.0+Craters(N);
    if(Body==5) return Noise(N*4+FVector(13,2,5),6)*10+FMath::Pow(FMath::Max(0.,Noise(N*15,5)*2),3)*12;
    if(Body==2) return Noise(N*5+FVector(5,3,14),6)*6;
    return 0;
}

float SolarModel::CloudDensity(const FVector& N)
{
    const double Warp=Noise(N*8,4);
    return Smooth(.02,.23,Noise(N*15+FVector(Warp*4,0,Warp),5));
}

FLinearColor SolarModel::SurfaceColor(int32 Body,const FVector& N)
{
    if(Body>=1 && Body<=5)
    {
        const FVector C=SurfaceRegion(Body,N,HeightKm(Body,N)).Color;
        return FLinearColor(C.X,C.Y,C.Z);
    }
    const double V=Noise(N*140+FVector(4,1,3),4);
    if(Body==0) { const double Grain=Noise(N*110,4); return FLinearColor(1.,.65+Grain*.5,.21+Grain*.2); }
    const double Lat=FMath::Asin(FMath::Clamp(N.Z,-1.,1.));
    const double Warp=Noise(N*9,5), Stripe=.5+.5*FMath::Sin(Lat*85+Warp*8);
    if(Body==6)
    {
        const double Belt=.5+.5*FMath::Sin(Lat*26+Warp*1.4);
        FLinearColor C=FMath::Lerp(FLinearColor(.38,.20,.12),FLinearColor(.79,.68,.49),Smooth(.12,.85,Belt));
        const double Spot=FMath::Exp(-FMath::Square((Lat+.36)/.10)-FMath::Square(FMath::Atan2(N.Y,N.X)/.24));
        return FMath::Lerp(C,FLinearColor(.56,.18,.09),Spot*.85)*(1+V*.17+.04*FMath::Sin(Lat*140+Warp*6));
    }
    if(Body==7) return FMath::Lerp(FLinearColor(.60,.49,.32),FLinearColor(.78,.68,.47),.5+.5*FMath::Sin(Lat*32+Warp*.8))*(1+V*.10+.025*FMath::Sin(Lat*145+Warp*3));
    if(Body==8) return FLinearColor(.40,.64,.68)*(.96+.04*Stripe);
    return FLinearColor(.34,.56,.67)*(.93+.07*Stripe+V*.05);
}

FSolarSurfaceRegion SolarModel::SurfaceRegion(int32 Body,const FVector& N,double H,double Slope)
{
    return FRegionRules().biome(Body,N.GetSafeNormal(1e-12,FVector::UpVector),H,Slope);
}

double SolarModel::SurfaceSlope(int32 Body,const FVector& N,double RadiusKm)
{
    // Centred 40 m height samples match the scale of vegetation placement.
    const FVector X=FVector::CrossProduct(N,FVector::UpVector).GetSafeNormal(1e-9,FVector::ForwardVector);
    const FVector Y=FVector::CrossProduct(N,X);
    const double Step=.02/FMath::Max(RadiusKm,1.);
    const double DX=(HeightKm(Body,(N+X*Step).GetSafeNormal())-HeightKm(Body,(N-X*Step).GetSafeNormal()))/.04;
    const double DY=(HeightKm(Body,(N+Y*Step).GetSafeNormal())-HeightKm(Body,(N-Y*Step).GetSafeNormal()))/.04;
    return 1-1/FMath::Sqrt(1+DX*DX+DY*DY);
}
