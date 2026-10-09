using UnrealBuildTool;

public class BigWorld : ModuleRules
{
    public BigWorld(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine", "InputCore", "WorldScapeCore", "WorldScapeNoise", "WorldScapeCommon", "WorldScapeVolume", "WorldScapeFoliages", "ProceduralMeshComponent", "Json", "JsonUtilities" });
        if (Target.bBuildEditor) PrivateDependencyModuleNames.Add("WorldScapeEditor");
    }
}
