"use client"

import * as React from "react"
import { ZONE_TYPES, ZONE_COLORS, type ZoneType } from "@/lib/constants"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Slider } from "@/components/ui/slider"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"

/**
 * Props for the ControlPanel component.
 */
export interface ControlPanelProps {
  /** Current confidence threshold (0.0 - 1.0) */
  confidenceThreshold: number
  /** Callback when confidence threshold changes */
  onConfidenceChange: (value: number) => void
  /** Set of currently selected zone types */
  selectedZoneTypes: Set<ZoneType>
  /** Callback when selected zone types change */
  onZoneTypesChange: (types: Set<ZoneType>) => void
  /** Count of zones per zone type */
  zoneTypeCounts: Record<ZoneType, number>
}

/**
 * Formats a zone type string into a human-readable label.
 * Example: "title_block" -> "Title Block"
 */
function formatZoneType(zoneType: ZoneType): string {
  return zoneType
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

/**
 * ControlPanel component for filtering controls.
 * Provides confidence threshold slider and zone type checkboxes.
 */
export function ControlPanel({
  confidenceThreshold,
  onConfidenceChange,
  selectedZoneTypes,
  onZoneTypesChange,
  zoneTypeCounts,
}: ControlPanelProps) {
  const allSelected = selectedZoneTypes.size === ZONE_TYPES.length
  const noneSelected = selectedZoneTypes.size === 0

  const handleSliderChange = (value: number[]) => {
    onConfidenceChange(value[0])
  }

  const handleCheckboxChange = (zoneType: ZoneType, checked: boolean) => {
    const newSet = new Set(selectedZoneTypes)
    if (checked) {
      newSet.add(zoneType)
    } else {
      newSet.delete(zoneType)
    }
    onZoneTypesChange(newSet)
  }

  const handleSelectAll = () => {
    onZoneTypesChange(new Set(ZONE_TYPES))
  }

  const handleDeselectAll = () => {
    if (confirm('Are you sure you want to deselect all zone types? No zones will be displayed.')) {
      onZoneTypesChange(new Set())
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Filter Controls</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Confidence Threshold Section */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label className="text-base font-medium">
              Confidence Threshold: {Math.round(confidenceThreshold * 100)}%
            </Label>
          </div>
          <Slider
            min={0}
            max={1}
            step={0.01}
            value={[confidenceThreshold]}
            onValueChange={handleSliderChange}
            className="w-full"
          />
        </div>

        {/* Zone Type Filters Section */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label className="text-base font-medium">Zone Type Filters</Label>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleSelectAll}
                disabled={allSelected}
              >
                Select All
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleDeselectAll}
                disabled={noneSelected}
              >
                Deselect All
              </Button>
            </div>
          </div>

          {/* Checkbox Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {ZONE_TYPES.map((zoneType) => {
              const count = zoneTypeCounts[zoneType] || 0
              const isChecked = selectedZoneTypes.has(zoneType)

              return (
                <div key={zoneType} className="flex items-center space-x-2">
                  <Checkbox
                    id={`zone-${zoneType}`}
                    checked={isChecked}
                    onCheckedChange={(checked) =>
                      handleCheckboxChange(zoneType, checked === true)
                    }
                  />
                  <Label
                    htmlFor={`zone-${zoneType}`}
                    className="flex items-center gap-2 cursor-pointer flex-1"
                  >
                    <div
                      className="size-3 rounded-full shrink-0"
                      style={{ backgroundColor: ZONE_COLORS[zoneType] }}
                      aria-hidden="true"
                    />
                    <span className="flex-1">{formatZoneType(zoneType)}</span>
                    <Badge variant="secondary" className="ml-auto">
                      {count}
                    </Badge>
                  </Label>
                </div>
              )
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
