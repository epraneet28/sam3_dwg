"use client";

import { useState, useMemo } from "react";
import { Upload, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useSegmentStructural, useHealth } from "@/lib/api-hooks";
import { ImageWithZones } from "@/components/ImageWithZones";
import { ControlPanel } from "@/components/ControlPanel";
import { ZONE_TYPES, DEFAULT_CONFIDENCE_THRESHOLD, type ZoneType } from "@/lib/constants";
import { useZoneHover } from "@/lib/hooks/useZoneHover";
import { useDebounce } from "@/lib/hooks/useDebounce";
import { filterZones, calculateZoneTypeCounts } from "@/lib/utils/zoneFilters";
import type { ZoneResult } from "@/lib/types";

export default function Home() {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [results, setResults] = useState<ZoneResult[] | null>(null);
  const [pageType, setPageType] = useState<string | null>(null);
  const [processingTime, setProcessingTime] = useState<number | null>(null);

  // Filter state
  const [confidenceThreshold, setConfidenceThreshold] = useState(DEFAULT_CONFIDENCE_THRESHOLD);
  const debouncedConfidenceThreshold = useDebounce(confidenceThreshold, 150);
  const [selectedZoneTypes, setSelectedZoneTypes] = useState<Set<ZoneType>>(
    new Set(ZONE_TYPES)
  );

  // Hover state
  const { hoveredZoneId, setHoveredZoneId } = useZoneHover();

  const { data: health } = useHealth();
  const { mutate: segment, isPending } = useSegmentStructural();

  // Derived state - filtered zones
  const filteredZones = useMemo(() => {
    if (!results) return null;
    return filterZones({
      zones: results,
      selectedZoneTypes,
      confidenceThreshold: debouncedConfidenceThreshold,
    });
  }, [results, selectedZoneTypes, debouncedConfidenceThreshold]);

  // Derived state - zone type counts
  const zoneTypeCounts = useMemo(() => {
    if (!results) return {} as Record<ZoneType, number>;
    return calculateZoneTypeCounts(results);
  }, [results]);

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setImageFile(file);
    const reader = new FileReader();
    reader.onload = (e) => {
      setSelectedImage(e.target?.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleSegment = async () => {
    if (!selectedImage || !imageFile) return;

    // Convert to base64 without data URI prefix
    const base64 = selectedImage.split(",")[1];

    segment(
      {
        image_base64: base64,
        return_masks: false,
        return_crops: false,
        classify_page_type: true,
      },
      {
        onSuccess: (data) => {
          setResults(data.zones);
          setPageType(data.page_type || null);
          setProcessingTime(data.processing_time_ms);
        },
        onError: (error: any) => {
          alert(error.response?.data?.detail || "Segmentation failed");
        },
      }
    );
  };

  const getZoneColor = (zoneType: string) => {
    const colors: Record<string, string> = {
      title_block: "bg-blue-500",
      revision_block: "bg-purple-500",
      plan_view: "bg-green-500",
      elevation_view: "bg-yellow-500",
      section_view: "bg-orange-500",
      detail_view: "bg-red-500",
      schedule_table: "bg-pink-500",
      notes_area: "bg-indigo-500",
      legend: "bg-cyan-500",
      grid_system: "bg-teal-500",
    };
    return colors[zoneType] || "bg-gray-500";
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold text-slate-900">
            SAM3 Drawing Zone Segmenter
          </h1>
          <p className="text-lg text-slate-600">
            Upload an engineering drawing to automatically segment it into semantic zones
          </p>
          {health && (
            <div className="flex items-center justify-center gap-2">
              <Badge variant={health.model_loaded ? "default" : "destructive"}>
                {health.status}
              </Badge>
              {health.gpu_available && (
                <Badge variant="outline">{health.gpu_name}</Badge>
              )}
            </div>
          )}
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Upload Section */}
          <Card>
            <CardHeader>
              <CardTitle>Upload Drawing</CardTitle>
              <CardDescription>
                Select a PNG or JPEG image of an engineering drawing
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div
                className="border-2 border-dashed border-slate-300 rounded-lg p-8 text-center cursor-pointer hover:border-slate-400 transition-colors"
                onClick={() => document.getElementById("file-input")?.click()}
              >
                {selectedImage ? (
                  <img
                    src={selectedImage}
                    alt="Selected drawing"
                    className="max-w-full max-h-96 mx-auto"
                  />
                ) : (
                  <div className="space-y-4">
                    <Upload className="mx-auto h-12 w-12 text-slate-400" />
                    <div>
                      <p className="text-sm font-medium text-slate-700">
                        Click to upload or drag and drop
                      </p>
                      <p className="text-xs text-slate-500">PNG, JPEG up to 10MB</p>
                    </div>
                  </div>
                )}
                <input
                  id="file-input"
                  type="file"
                  accept="image/png,image/jpeg"
                  className="hidden"
                  onChange={handleImageSelect}
                />
              </div>

              <Button
                onClick={handleSegment}
                disabled={!selectedImage || isPending}
                className="w-full"
                size="lg"
              >
                {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {isPending ? "Segmenting..." : "Segment Drawing"}
              </Button>
            </CardContent>
          </Card>

          {/* Filter Controls Section */}
          {results && results.length > 0 && (
            <ControlPanel
              confidenceThreshold={confidenceThreshold}
              onConfidenceChange={setConfidenceThreshold}
              selectedZoneTypes={selectedZoneTypes}
              onZoneTypesChange={setSelectedZoneTypes}
              zoneTypeCounts={zoneTypeCounts}
            />
          )}

          {/* Results Section */}
          <Card>
            <CardHeader>
              <CardTitle>Segmentation Results</CardTitle>
              <CardDescription>
                {results
                  ? `Showing ${filteredZones?.length || 0} of ${results.length} zones (${processingTime?.toFixed(0)}ms)`
                  : "Results will appear here after segmentation"}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {pageType && (
                <div className="mb-4">
                  <p className="text-sm font-medium text-slate-700 mb-2">
                    Page Type:
                  </p>
                  <Badge variant="outline" className="text-base">
                    {pageType}
                  </Badge>
                </div>
              )}

              {filteredZones && filteredZones.length > 0 ? (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {filteredZones.map((zone) => (
                    <div
                      key={zone.zone_id}
                      onMouseEnter={() => setHoveredZoneId(zone.zone_id)}
                      onMouseLeave={() => setHoveredZoneId(null)}
                      className={`flex items-center justify-between p-3 rounded-lg border transition-colors ${
                        hoveredZoneId === zone.zone_id
                          ? "bg-slate-100 border-slate-400"
                          : "bg-white border-slate-200 hover:bg-slate-50"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <div
                          className={`w-3 h-3 rounded-full ${getZoneColor(
                            zone.zone_type
                          )}`}
                        />
                        <div>
                          <p className="font-medium text-sm text-slate-900">
                            {zone.zone_type.replace(/_/g, " ").toUpperCase()}
                          </p>
                          <p className="text-xs text-slate-500">
                            Confidence: {(zone.confidence * 100).toFixed(1)}%
                          </p>
                        </div>
                      </div>
                      <Badge variant="secondary">
                        {zone.bbox.map((v) => Math.round(v)).join(", ")}
                      </Badge>
                    </div>
                  ))}
                </div>
              ) : results && results.length > 0 && filteredZones?.length === 0 ? (
                <p className="text-sm text-slate-500 text-center py-8">
                  No zones match current filters. Try lowering the confidence threshold or selecting more zone types.
                </p>
              ) : results && results.length === 0 ? (
                <p className="text-sm text-slate-500 text-center py-8">
                  No zones detected. Try adjusting the confidence threshold or use a
                  different image.
                </p>
              ) : (
                <p className="text-sm text-slate-500 text-center py-8">
                  Upload and segment a drawing to see results
                </p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Visualization Section */}
        {selectedImage && filteredZones && filteredZones.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Zone Visualization</CardTitle>
              <CardDescription>
                {filteredZones.length === results?.length
                  ? "All detected zones highlighted on the original image"
                  : `${filteredZones.length} filtered zones highlighted (${results?.length} total detected)`}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ImageWithZones
                imageSrc={selectedImage}
                zones={filteredZones}
                hoveredZoneId={hoveredZoneId}
                onZoneHover={setHoveredZoneId}
              />
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
