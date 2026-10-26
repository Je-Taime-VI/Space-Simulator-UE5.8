#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SolarModel.h"
#include "SolarSystemActor.generated.h"

class AWorldScapeRoot;
class UStaticMeshComponent;
class UProceduralMeshComponent;
class UMaterialInstanceDynamic;
class UMaterialInterface;
class UDirectionalLightComponent;
class USkyLightComponent;
class UPostProcessComponent;
class USkyAtmosphereComponent;
class UVolumetricCloudComponent;
class UHierarchicalInstancedStaticMeshComponent;
class USolarTerrainNoise;
class UStaticMesh;

UCLASS()
class BIGWORLD_API ASolarSystemActor : public AActor
{
    GENERATED_BODY()
public:
    ASolarSystemActor();
    virtual void BeginPlay() override;
    virtual void PostRegisterAllComponents() override;
    virtual void Tick(float DeltaSeconds) override;
    virtual bool ShouldTickIfViewportsOnly() const override { return true; }
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Solar|Catalogue") TArray<FSolarBody> Bodies;
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Solar|Materials") TObjectPtr<UStaticMesh> PlanetMesh;
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Solar|Materials") TArray<TObjectPtr<UMaterialInterface>> BodyMaterials;
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Solar|Materials") TArray<TObjectPtr<UMaterialInterface>> TerrainMaterials;
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Solar|Materials") TObjectPtr<UMaterialInterface> AtmosphereMaterial;
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Solar|Materials") TObjectPtr<UMaterialInterface> CloudMaterial;
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Solar|Materials") TObjectPtr<UMaterialInterface> VolumeCloudMaterial;
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Solar|Materials") TObjectPtr<UMaterialInterface> RingMaterial;
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Solar|Materials") TObjectPtr<UMaterialInterface> OceanMaterial;
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Solar|Time") double SimulationSeconds=0;
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Solar|Time") double TimeScale=1;
    UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="Solar") int32 FocusIndex=3;
    UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="Solar") bool bSurfaceMode=false;
    UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="Solar") TObjectPtr<AWorldScapeRoot> ActiveTerrain;
    UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="Solar") TObjectPtr<UDirectionalLightComponent> SunLight;
    UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="Solar|Lighting") TObjectPtr<USkyLightComponent> SurfaceSkyLight;
    UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="Solar|Lighting") TObjectPtr<UPostProcessComponent> LightingExposure;
    // Reference illuminance before atmospheric extinction; not a photometric ephemeris.
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Solar|Lighting",meta=(ClampMin="1")) double SolarIlluminanceAtOneAU=120000;
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Solar|Lighting",meta=(ClampMin="-10",ClampMax="10")) float ExposureCompensation=0;
    // Deterministic distance compensation, independent of image brightness or viewing direction.
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Solar|Lighting") bool bCompensateExposureForSolarDistance=true;
    UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="Solar") TObjectPtr<USkyAtmosphereComponent> LocalAtmosphere;
    UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="Solar") TObjectPtr<UVolumetricCloudComponent> VolumeClouds;
    UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="Solar") float TerrainBlend=0;
    UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="Solar") TObjectPtr<UHierarchicalInstancedStaticMeshComponent> Trees;
    UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="Solar") TObjectPtr<UHierarchicalInstancedStaticMeshComponent> Grass;

    UFUNCTION(BlueprintCallable,Category="Solar") void FocusBody(int32 Index);
    UFUNCTION(BlueprintCallable,Category="Solar") void ResetCatalogue();
    UFUNCTION(BlueprintCallable,Category="Solar") bool ReframeBody(int32 Index);
    UFUNCTION(BlueprintCallable,Category="Solar") bool VisitSurface(double LatitudeDeg=25, double LongitudeDeg=0, double HeightMeters=150);
    UFUNCTION(BlueprintCallable,Category="Solar") void SetSimulationTime(double Seconds);
    UFUNCTION(BlueprintCallable,Category="Solar") void SetTimeScale(double Scale);
    UFUNCTION(BlueprintCallable,Category="Solar") void PreviewSystem();
    UFUNCTION(BlueprintCallable,Category="Solar") void RebuildPreview();
    UFUNCTION(BlueprintCallable,Category="Solar") FString GetDiagnostics() const;
    UFUNCTION(BlueprintCallable,Category="Solar") bool ExportProceduralTextures(const FString& Directory,int32 Width=1024);
    UFUNCTION(BlueprintCallable,Category="Solar") FString ValidateModel() const;
    UFUNCTION(BlueprintPure,Category="Solar") float GetCloudCoverage(FVector Direction) const;
    UFUNCTION(BlueprintCallable,Category="Solar|Surface") FString GetSurfaceRegion(int32 BodyIndex,FVector Direction,float Slope=-1) const;
    FVector GetFocusSunDirection() const;
    double GetGroundRadiusKm(const FVector& N) const;
    FVector GetLogicalPositionKm() const;
    void UpdateVisuals(const FVector& ObserverLocalCm);
private:
    void CreateVisuals();
    void ClearTerrain();
    void EnsureTerrain();
    void ConfigureAtmosphere();
    void UpdateTerrain(float DeltaSeconds, const FVector& CameraPosition);
    void BuildVegetation(const FVector& Direction);
    UPROPERTY(Transient) TArray<TObjectPtr<UStaticMeshComponent>> Spheres;
    UPROPERTY(Transient) TArray<TObjectPtr<UStaticMeshComponent>> Shells;
    UPROPERTY(Transient) TArray<TObjectPtr<UMaterialInstanceDynamic>> SurfaceMIDs;
    UPROPERTY(Transient) TArray<TObjectPtr<UMaterialInstanceDynamic>> ShellMIDs;
    UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> Clouds;
    UPROPERTY(Transient) TArray<TObjectPtr<UProceduralMeshComponent>> PlanetRings;
    UPROPERTY(Transient) TArray<TObjectPtr<UMaterialInstanceDynamic>> RingMIDs;
    UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> CloudMID;
    UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> VolumeCloudMID;
    UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> TerrainMID;
    UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> OceanMID;
    UPROPERTY(Transient) TObjectPtr<USolarTerrainNoise> ActiveNoise;
    TArray<FVector> Positions;
    TArray<FQuat> Rotations;
    FVector VegetationCenter=FVector::ZeroVector;
    double VegetationTimer=0;
    bool bInitialized=false;
    int32 AtmosphereFocus=INDEX_NONE;
    double TerrainWarmup=0;
};
