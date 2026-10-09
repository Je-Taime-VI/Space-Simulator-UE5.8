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
    Add(TEXT("Earth"),TEXT("地球"),6371.0084,398600.435507,1.00000261,.01671123,0,0,102.93768193,100.46457166,.99726968,23.43928,100,true);
    Result.Last().bOcean=true;
    Add(TEXT("Moon"),TEXT("月球"),1737.4,4902.800118,384400/AU,.0549,5.145,125.08,318.15,218.316,27.321661,6.68,0,true);
    Result.Last().ParentIndex=3; Result.Last().PeriodDays=27.321661; Result.Last().bTidalLock=true;
    Add(TEXT("Mars"),TEXT("火星"),3389.5,42828.375816,1.52371034,.09339410,1.84969142,49.55953891,-23.94362959,-4.55343205,1.02595676,25.19,80,true);
    Add(TEXT("Jupiter"),TEXT("木星"),69911,126712764.1,5.202887,.04838624,1.30439695,100.47390909,14.72847983,34.39644051,.41354,3.13,0,false);
    Add(TEXT("Saturn"),TEXT("土星"),58232,37940584.84,9.53667594,.05386179,2.48599187,113.66242448,92.59887831,49.95424423,.44401,26.73,0,false);
    Add(TEXT("Uranus"),TEXT("天王星"),25362,5794556.4,19.18916464,.04725744,.77263783,74.01692503,170.95427630,313.23810451,.71833,97.77,0,false);
    Add(TEXT("Neptune"),TEXT("海王星"),24622,6836527.1,30.06992276,.00859048,1.77004347,131.78422574,44.96476227,-55.12002969,.67125,28.32,0,false);
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

void SolarModel::Evaluate(const TArray<FSolarBody>& Bodies,double Seconds,TArray<FVector>& P,TArray<FQuat>& Q)
{
    P.SetNum(Bodies.Num()); Q.SetNum(Bodies.Num());
    for(int I=0;I<Bodies.Num();++I) { P[I]=OrbitPosition(Bodies[I],Seconds); if(Bodies[I].ParentIndex>0)P[I]+=P[Bodies[I].ParentIndex]; }
    // Earth elements describe the Earth-Moon barycentre.
    if(Bodies.Num()>4) { const FVector Correction=(P[4]-P[3])*(Bodies[4].MuKm3S2/(Bodies[3].MuKm3S2+Bodies[4].MuKm3S2)); P[3]-=Correction; P[4]-=Correction; }
    for(int I=0;I<Bodies.Num();++I)
    {
        const auto& B=Bodies[I];
        if(B.bTidalLock) Q[I]=FRotationMatrix::MakeFromXZ((P[B.ParentIndex]-P[I]).GetSafeNormal(),FVector::UpVector).ToQuat();
        else Q[I]=FQuat(FVector::RightVector,FMath::DegreesToRadians(B.AxialTiltDeg))*FQuat(FVector::UpVector,2*PI*FMath::Fmod(Seconds/(B.SpinDays*86400),1.));
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
    const double V=Noise(N*140+FVector(4,1,3),4), Latitude=FMath::Abs(N.Z);
    if(Body==0) { const double Grain=Noise(N*110,4); return FLinearColor(1.,.65+Grain*.5,.21+Grain*.2); }
    if(Body==3)
    {
        const double H=HeightKm(Body,N);
        if(Latitude>.95+Noise(N*32,3)*.018 || H>4.) return FLinearColor(.81,.89,.91)*(1+V*.16);
        if(H<0) return FMath::Lerp(FLinearColor(.018,.09,.16),FLinearColor(.035,.26,.30),FMath::Exp(H*2));
        if(H<.065) return FLinearColor(.46,.40,.24);
        const double Desert=Smooth(.08,.24,Noise(N*8+FVector(7,7,3),4))*(1-Smooth(.48,.7,Latitude));
        FLinearColor C=FMath::Lerp(FLinearColor(.052,.145,.049),FLinearColor(.42,.30,.15),Desert);
        C=FMath::Lerp(C,FLinearColor(.23,.22,.20),Smooth(1.,3.8,H));
        return C*(.95+V*.5);
    }
    if(Body==1 || Body==4)
    {
        const double Mare=Smooth(-.03,.13,Noise(N*3+FVector(8,Body,3),4));
        return FMath::Lerp(FLinearColor(.14,.145,.15),FLinearColor(.4,.39,.37),Mare)*FMath::Clamp(1+V*.6+Craters(N)*.20,.4,1.3);
    }
    if(Body==5) { if(Latitude>.965)return FLinearColor(.8,.78,.72); return FMath::Lerp(FLinearColor(.20,.08,.045),FLinearColor(.53,.26,.13),FMath::Clamp(.5+Noise(N*8,5)*2,0.,1.))*(1+V*.4); }
    if(Body==2) return FLinearColor(.72,.56,.30)*(0.85+Noise(N*18+FVector(2,5,3),5)*.55);
    const double Lat=FMath::Asin(FMath::Clamp(N.Z,-1.,1.));
    const double Warp=Noise(N*9,5), Stripe=.5+.5*FMath::Sin(Lat*85+Warp*8);
    if(Body==6)
    {
        FLinearColor C=FMath::Lerp(FLinearColor(.38,.20,.12),FLinearColor(.79,.68,.49),Stripe);
        const double Spot=FMath::Exp(-FMath::Square((Lat+.36)/.10)-FMath::Square(FMath::Atan2(N.Y,N.X)/.24));
        return FMath::Lerp(C,FLinearColor(.56,.18,.09),Spot*.85)*(1+V*.17);
    }
    if(Body==7) return FMath::Lerp(FLinearColor(.51,.39,.23),FLinearColor(.80,.70,.46),.5+.5*FMath::Sin(Lat*105+Warp*3))*(1+V*.10);
    if(Body==8) return FLinearColor(.32,.62,.67)*(.90+.10*Stripe);
    return FLinearColor(.10,.27,.61)*(.76+.24*Stripe+V*.1);
}
