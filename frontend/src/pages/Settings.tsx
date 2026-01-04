/**
 * Settings Page - Minimalist Prompt Configuration
 *
 * Clean, focused UI for managing SAM3 zone prompts.
 */

import { useState, useEffect } from 'react';
import { ArrowPathIcon, CheckIcon, ChevronDownIcon } from '@heroicons/react/24/outline';
import { useStore, usePromptConfig, useInferenceSettings, useConfigVersion } from '../store';
import { api } from '../api/client';
import type { ZonePromptConfig, InferenceSettings } from '../types';
import { getZoneColor } from '../utils/constants';

export default function Settings() {
  const promptConfig = usePromptConfig();
  const inferenceSettings = useInferenceSettings();
  const configVersion = useConfigVersion();
  const { setPromptConfig, updatePrompt, togglePromptEnabled, setInferenceSettings } = useStore();

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [toast, setToast] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [expandedZone, setExpandedZone] = useState<string | null>(null);

  // Load config on mount
  useEffect(() => {
    loadConfig();
  }, []);

  // Auto-hide toast
  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [toast]);

  const loadConfig = async () => {
    setLoading(true);
    try {
      const config = await api.getPromptConfig();
      setPromptConfig(config.prompts, config.inference, config.version);
    } catch (err) {
      setToast({ type: 'error', message: 'Failed to load configuration' });
      console.error('Failed to load config:', err);
    } finally {
      setLoading(false);
    }
  };

  const saveConfig = async () => {
    setSaving(true);
    try {
      const config = await api.updatePromptConfig({
        prompts: promptConfig,
        inference: inferenceSettings,
      });
      setPromptConfig(config.prompts, config.inference, config.version);
      setHasChanges(false);
      setToast({ type: 'success', message: 'Saved' });
    } catch (err) {
      setToast({ type: 'error', message: 'Failed to save' });
      console.error('Failed to save config:', err);
    } finally {
      setSaving(false);
    }
  };

  const resetConfig = async () => {
    if (!confirm('Reset all prompts to defaults?')) return;
    setSaving(true);
    try {
      const config = await api.resetPromptConfig();
      setPromptConfig(config.prompts, config.inference, config.version);
      setHasChanges(false);
      setToast({ type: 'success', message: 'Reset to defaults' });
    } catch (err) {
      setToast({ type: 'error', message: 'Failed to reset' });
      console.error('Failed to reset config:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleToggleEnabled = (zoneType: string) => {
    togglePromptEnabled(zoneType);
    setHasChanges(true);
  };

  const handlePromptChange = (zoneType: string, value: string) => {
    updatePrompt(zoneType, { primary_prompt: value });
    setHasChanges(true);
  };

  const handleInferenceChange = (settings: Partial<InferenceSettings>) => {
    setInferenceSettings(settings);
    setHasChanges(true);
  };

  const enabledCount = promptConfig.filter((p) => p.enabled).length;

  return (
    <div className="h-full overflow-y-auto bg-slate-900">
      <div className="max-w-3xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-xl font-semibold text-white">Settings</h1>
            <p className="text-sm text-slate-500 mt-1">
              {enabledCount} of {promptConfig.length} zones enabled
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={resetConfig}
              disabled={saving}
              className="px-3 py-1.5 text-sm text-slate-400 hover:text-white transition-colors disabled:opacity-50"
            >
              Reset
            </button>
            <button
              onClick={saveConfig}
              disabled={saving || !hasChanges}
              className={`relative flex items-center gap-2 px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${
                hasChanges
                  ? 'bg-blue-600 hover:bg-blue-700 text-white'
                  : 'bg-slate-800 text-slate-400'
              } disabled:opacity-50`}
            >
              {saving ? (
                <ArrowPathIcon className="w-4 h-4 animate-spin" />
              ) : (
                <CheckIcon className="w-4 h-4" />
              )}
              Save
              {hasChanges && (
                <span className="absolute -top-1 -right-1 w-2 h-2 bg-amber-500 rounded-full" />
              )}
            </button>
          </div>
        </div>

        {/* Confidence Slider - Compact */}
        <div className="mb-8 p-4 bg-slate-800/50 rounded-xl">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm text-slate-300">Confidence Threshold</span>
            <span className="text-sm font-mono text-blue-400">
              {(inferenceSettings.confidence_threshold * 100).toFixed(0)}%
            </span>
          </div>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={inferenceSettings.confidence_threshold}
            onChange={(e) =>
              handleInferenceChange({ confidence_threshold: parseFloat(e.target.value) })
            }
            className="w-full h-1.5 bg-slate-700 rounded-full appearance-none cursor-pointer accent-blue-500"
          />
        </div>

        {/* Zone List */}
        <div className="space-y-1">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <ArrowPathIcon className="w-6 h-6 text-slate-500 animate-spin" />
            </div>
          ) : (
            promptConfig.map((prompt) => (
              <ZoneRow
                key={prompt.zone_type}
                prompt={prompt}
                isExpanded={expandedZone === prompt.zone_type}
                onToggle={() => handleToggleEnabled(prompt.zone_type)}
                onExpand={() =>
                  setExpandedZone(expandedZone === prompt.zone_type ? null : prompt.zone_type)
                }
                onPromptChange={(value) => handlePromptChange(prompt.zone_type, value)}
              />
            ))
          )}
        </div>

        {/* Version footer */}
        <div className="mt-8 text-center text-xs text-slate-600">
          Config v{configVersion}
        </div>
      </div>

      {/* Toast notification */}
      {toast && (
        <div
          className={`fixed bottom-6 right-6 px-4 py-2 rounded-lg text-sm font-medium shadow-lg transition-all ${
            toast.type === 'success'
              ? 'bg-green-500/90 text-white'
              : 'bg-red-500/90 text-white'
          }`}
        >
          {toast.message}
        </div>
      )}
    </div>
  );
}

interface ZoneRowProps {
  prompt: ZonePromptConfig;
  isExpanded: boolean;
  onToggle: () => void;
  onExpand: () => void;
  onPromptChange: (value: string) => void;
}

function ZoneRow({ prompt, isExpanded, onToggle, onExpand, onPromptChange }: ZoneRowProps) {
  const color = getZoneColor(prompt.zone_type as any);

  return (
    <div
      className={`rounded-lg transition-all ${
        prompt.enabled ? 'bg-slate-800/80' : 'bg-slate-800/30'
      }`}
    >
      {/* Main row */}
      <div className="flex items-center gap-3 px-4 py-3">
        {/* Toggle */}
        <button
          onClick={onToggle}
          className={`w-9 h-5 rounded-full relative transition-colors flex-shrink-0 ${
            prompt.enabled ? 'bg-blue-600' : 'bg-slate-600'
          }`}
        >
          <span
            className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform ${
              prompt.enabled ? 'left-4' : 'left-0.5'
            }`}
          />
        </button>

        {/* Zone indicator + name */}
        <div className="flex items-center gap-2 min-w-0 flex-1">
          <div
            className="w-2 h-2 rounded-full flex-shrink-0"
            style={{ backgroundColor: color }}
          />
          <span
            className={`text-sm font-medium truncate ${
              prompt.enabled ? 'text-white' : 'text-slate-500'
            }`}
          >
            {prompt.zone_type.replace(/_/g, ' ')}
          </span>
        </div>

        {/* Expand button */}
        <button
          onClick={onExpand}
          className={`p-1 rounded transition-colors ${
            prompt.enabled
              ? 'text-slate-400 hover:text-white'
              : 'text-slate-600'
          }`}
        >
          <ChevronDownIcon
            className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
          />
        </button>
      </div>

      {/* Expanded content */}
      {isExpanded && (
        <div className="px-4 pb-4">
          <input
            type="text"
            value={prompt.primary_prompt}
            onChange={(e) => onPromptChange(e.target.value)}
            disabled={!prompt.enabled}
            placeholder="Detection prompt..."
            className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 disabled:opacity-50"
          />
          {prompt.alternate_prompts.length > 0 && (
            <div className="mt-2 text-xs text-slate-500">
              Also matches: {prompt.alternate_prompts.slice(0, 2).join(', ')}
              {prompt.alternate_prompts.length > 2 && ` +${prompt.alternate_prompts.length - 2} more`}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
