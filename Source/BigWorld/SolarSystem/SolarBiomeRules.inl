// Shared C++/HLSL rules. Only the small math/noise adapters differ between hosts.
// Climate values are procedural distribution indices, not simulated weather.
FSolarSurfaceRegion biome(int body, float3 n, float h, float slope)
{
    FSolarSurfaceRegion r;
    r.Sand=0; r.Rock=0; r.Soil=1; r.Snow=0;
    r.Temperature=0; r.Moisture=0; r.Vegetation=0; r.Water=0;
    r.Color=float3(.25,.25,.25);
    float lat=abs(axisZ(n));
    float steep=smoothstep(.035,.18,slope);
    float province=saturate(.5+noise(n*5+float3(17,3,8),3)*1.8);
    float rock=0, sand=0, snow=0;
    float3 soilColor=float3(.25,.25,.25),rockColor=float3(.24,.24,.24);
    float3 sandColor=float3(.45,.34,.19),snowColor=float3(.81,.87,.90);
    if(body==3)
    {
        r.Water=h<0 ? 1 : 0;
        r.Temperature=saturate(1-pow(lat,1.35)*1.12-max(h,0)*.075);
        float equatorial=1-smoothstep(.12,.40,lat);
        float dryBelt=exp(-pow((lat-.50)/.18,2));
        r.Moisture=saturate(.58+noise(n*4.5+float3(6,14,2),3)*1.25+equatorial*.18-dryBelt*.32);
        float snowline=lerp(4.8,.15,pow(lat,2))+noise(n*6+float3(9,3,5),2)*.3;
        snow=max(smoothstep(.940,.980,lat),smoothstep(snowline-.28,snowline+.28,h));
        snow*=1-steep*.65;
        float desert=(1-smoothstep(.28,.44,r.Moisture))*smoothstep(.22,.5,r.Temperature);
        desert*=1-smoothstep(1.2,3.2,h);
        float beach=(1-smoothstep(.008,.045,h))*(1-steep);
        sand=max(beach,desert);
        rock=max(steep,smoothstep(1.2,3.5,h)*.65);
        float cold=1-smoothstep(.18,.42,r.Temperature);
        soilColor=lerp(float3(.23,.20,.10),float3(.046,.13,.045),smoothstep(.32,.7,r.Moisture));
        soilColor=lerp(soilColor,float3(.18,.16,.11),cold*.7);
        rockColor=float3(.23,.22,.20);
        sandColor=lerp(float3(.46,.40,.24),float3(.43,.31,.16),desert);
    }
    else if(body==5)
    {
        // Cold dusty plains, exposed basalt and separate polar caps; no vegetation.
        snow=smoothstep(axisZ(n)>0 ? .952 : .965,axisZ(n)>0 ? .981 : .989,lat);
        snow*=1-steep*.5;
        sand=(1-province)*.72*(1-steep);
        rock=max(steep,.10+province*.55+smoothstep(2,7,h)*.15);
        soilColor=float3(.40,.18,.085); rockColor=float3(.21,.12,.075);
        sandColor=float3(.50,.25,.12); snowColor=float3(.80,.78,.72);
    }
    else if(body==2)
    {
        // Dry volcanic lowlands / rough highlands. No terrestrial snow or beach.
        rock=max(steep,.40+province*.35+smoothstep(1,5,h)*.2);
        soilColor=float3(.34,.245,.15); rockColor=float3(.27,.20,.125);
    }
    else
    {
        // Airless regolith and exposed rock. Dark plains are a visual analogue.
        float plain=smoothstep(-.03,.13,noise(n*3+float3(8,body,3),4));
        rock=max(steep,.10+province*.18+smoothstep(.8,2.8,h)*.2);
        soilColor=lerp(float3(.14,.145,.15),float3(.40,.39,.37),plain);
        rockColor=soilColor*.82;
    }
    r.Snow=saturate(snow);
    r.Rock=(1-r.Snow)*saturate(rock);
    r.Sand=(1-r.Snow-r.Rock)*saturate(sand);
    r.Soil=max(0,1-r.Snow-r.Rock-r.Sand);
    r.Color=r.Sand*sandColor+r.Rock*rockColor+r.Soil*soilColor+r.Snow*snowColor;
    if(body==3)
    {
        r.Vegetation=(1-r.Water)*r.Soil*smoothstep(.32,.57,r.Moisture)*smoothstep(.18,.5,r.Temperature);
        r.Vegetation*=1-smoothstep(2.0,3.8,h);
        if(r.Water>0)r.Color=lerp(float3(.018,.09,.16),float3(.035,.26,.30),exp(h*2));
    }
    return r;
}
