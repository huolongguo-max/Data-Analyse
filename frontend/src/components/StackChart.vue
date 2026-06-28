<script setup>
import { computed, ref, watch } from "vue";

const props = defineProps({
  rows: { type: Array, default: () => [] },
  note: { type: String, default: "" },
  singleSeriesLegend: { type: Boolean, default: false },
  sortVisibleAscending: { type: Boolean, default: false },
  hideTrackBackground: { type: Boolean, default: false },
});

const tooltip = ref({ visible: false, x: 0, y: 0, label: "", segments: [], total: 0 });
const selectedLegend = ref("");

const COLORS = [
  ["#4fc3f7", "#1a73e8"],
  ["#ffcc80", "#ff9f43"],
  ["#a5d6a7", "#43a047"],
  ["#f8b4d9", "#ec4899"],
  ["#c4b5fd", "#7c3aed"],
  ["#b2dfdb", "#26a69a"],
  ["#ffe082", "#f59e0b"],
  ["#90caf9", "#2563eb"],
];

function totalOf(segments = []) {
  return segments.reduce((sum, segment) => sum + Number(segment.value || 0), 0);
}

const legendItems = computed(() => {
  const labels = [];
  const seen = new Set();
  props.rows.forEach((row) => {
    row.segments.forEach((segment) => {
      if (!seen.has(segment.label)) {
        seen.add(segment.label);
        labels.push(segment.label);
      }
    });
  });
  return labels.map((label, index) => ({ label, index }));
});

const legendIndexMap = computed(() => new Map(legendItems.value.map((item) => [item.label, item.index])));

watch(
  legendItems,
  (items) => {
    if (!props.singleSeriesLegend || !items.length) {
      selectedLegend.value = "";
      return;
    }
    if (selectedLegend.value && !items.some((item) => item.label === selectedLegend.value)) {
      selectedLegend.value = "";
    }
  },
  { immediate: true }
);

const preparedRows = computed(() => {
  const scopedRows = props.rows.map((row) => {
    const visibleSegments =
      props.singleSeriesLegend && selectedLegend.value
        ? row.segments.filter((segment) => segment.label === selectedLegend.value)
        : row.segments;
    return {
      ...row,
      fullTotal: totalOf(row.segments),
      visibleSegments,
      visibleTotal: totalOf(visibleSegments),
    };
  });

  if (props.sortVisibleAscending) {
    scopedRows.sort(
      (left, right) => left.visibleTotal - right.visibleTotal || String(left.label).localeCompare(String(right.label), "zh-CN")
    );
  }

  return scopedRows;
});

const maxTotal = computed(() => Math.max(1, ...preparedRows.value.map((row) => row.visibleTotal)));

function colorPair(label) {
  const index = legendIndexMap.value.get(label) ?? 0;
  return COLORS[index % COLORS.length];
}

function segmentWidth(row) {
  return `${(row.visibleTotal / maxTotal.value) * 100}%`;
}

function segPct(total, segment) {
  if (!total) {
    return "0%";
  }
  return `${((Number(segment.value || 0) / total) * 100).toFixed(1)}%`;
}

function showTip(event, row) {
  const rect = event.currentTarget.closest(".stack-chart").getBoundingClientRect();
  tooltip.value = {
    visible: true,
    x: event.clientX - rect.left + 12,
    y: event.clientY - rect.top - 8,
    label: row.label,
    segments: row.visibleSegments,
    total: row.fullTotal,
  };
}

function moveTip(event) {
  if (!tooltip.value.visible) {
    return;
  }
  const rect = event.currentTarget.closest(".stack-chart").getBoundingClientRect();
  tooltip.value.x = event.clientX - rect.left + 12;
  tooltip.value.y = event.clientY - rect.top - 8;
}

function hideTip() {
  tooltip.value.visible = false;
}

function selectLegend(label) {
  if (!props.singleSeriesLegend) {
    return;
  }
  selectedLegend.value = selectedLegend.value === label ? "" : label;
}
</script>

<template>
  <div v-if="!rows.length" class="empty-state">当前没有可展示的数据。</div>
  <div v-else class="stack-chart">
    <div class="stack-legend">
      <template v-if="singleSeriesLegend">
        <button
          v-for="item in legendItems"
          :key="item.label"
          class="stack-legend-item"
          :class="{
            active: !selectedLegend || selectedLegend === item.label,
            inactive: selectedLegend && selectedLegend !== item.label,
          }"
          type="button"
          @click="selectLegend(item.label)"
        >
          <span class="stack-legend-dot" :style="{ background: colorPair(item.label)[1] }"></span>
          {{ item.label }}
        </button>
      </template>
      <template v-else>
        <span v-for="item in legendItems" :key="item.label" class="stack-legend-item stack-legend-item--static">
          <span class="stack-legend-dot" :style="{ background: colorPair(item.label)[1] }"></span>
          {{ item.label }}
        </span>
      </template>
    </div>

    <div
      v-for="row in preparedRows"
      :key="row.label"
      class="stack-row"
      @mouseenter="(event) => showTip(event, row)"
      @mousemove="moveTip"
      @mouseleave="hideTip"
    >
      <div class="stack-label" :title="row.label">{{ row.label }}</div>
      <div class="stack-track-wrap">
        <div class="stack-track-main">
          <div v-if="!hideTrackBackground" class="stack-track-bg"></div>
          <div class="stack-track-fill" :style="{ width: segmentWidth(row) }">
            <div
              v-for="segment in row.visibleSegments"
              :key="segment.label"
              class="stack-seg"
              :style="{
                flex: Number(segment.value) || 0,
                background: `linear-gradient(90deg, ${colorPair(segment.label)[0]}, ${colorPair(segment.label)[1]})`,
              }"
            ></div>
          </div>
        </div>
        <span class="stack-row-total">{{ row.visibleTotal.toLocaleString("zh-CN") }}</span>
      </div>
    </div>

    <div v-if="tooltip.visible" class="chart-tooltip" :style="{ left: `${tooltip.x}px`, top: `${tooltip.y}px` }">
      <div class="chart-tooltip-title">{{ tooltip.label }}</div>
      <div class="chart-tooltip-total">{{ singleSeriesLegend ? "片区合计：" : "合计：" }}{{ tooltip.total.toLocaleString("zh-CN") }}</div>
      <div v-for="segment in tooltip.segments" :key="segment.label" class="chart-tooltip-row">
        <span class="chart-tooltip-dot" :style="{ background: colorPair(segment.label)[1] }"></span>
        <span class="chart-tooltip-name">{{ segment.label }}</span>
        <span class="chart-tooltip-val">{{ Number(segment.value || 0).toLocaleString("zh-CN") }}</span>
        <span class="chart-tooltip-pct">{{ segPct(tooltip.total, segment) }}</span>
      </div>
    </div>

    <div v-if="note" class="mini-note">{{ note }}</div>
  </div>
</template>

<style scoped>
.stack-chart {
  position: relative;
}

.stack-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 12px;
  margin-bottom: 12px;
}

.stack-legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border: 1px solid #d8dee8;
  border-radius: 999px;
  background: #fff;
  font-size: 12px;
  color: #777;
  font-weight: 500;
  line-height: 1;
  font-family: inherit;
  appearance: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

.stack-legend-item--static {
  cursor: default;
}

.stack-legend-item.active {
  border-color: #8bb8ff;
  background: #eef5ff;
  color: #2257a6;
}

.stack-legend-item.inactive {
  opacity: 0.58;
}

.stack-legend-item:hover {
  border-color: #b8c7de;
}

.stack-legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 3px;
  flex-shrink: 0;
}

.stack-row {
  display: grid;
  grid-template-columns: 100px 1fr;
  align-items: center;
  gap: 12px;
  cursor: default;
}

.stack-label {
  font-size: 12px;
  font-weight: 500;
  color: #555;
  text-align: right;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.stack-track-wrap {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.stack-track-main {
  position: relative;
  display: flex;
  align-items: center;
  min-width: 0;
  height: 28px;
}

.stack-track-bg {
  position: absolute;
  inset: 0;
  border-radius: 5px;
  background: #f0f2f5;
  width: 100%;
  height: 28px;
  pointer-events: none;
}

.stack-track-fill {
  position: relative;
  display: flex;
  height: 28px;
  border-radius: 5px;
  overflow: hidden;
  min-width: 0;
  transition: width 0.4s ease;
  z-index: 1;
}

.stack-seg {
  height: 100%;
}

.stack-row-total {
  position: relative;
  z-index: 2;
  min-width: 0;
  white-space: normal;
  overflow-wrap: anywhere;
  font-size: 12px;
  font-weight: 600;
  color: #444;
  text-align: right;
}

.chart-tooltip {
  position: absolute;
  z-index: 100;
  pointer-events: none;
  min-width: 200px;
  padding: 10px 14px;
  border-radius: 10px;
  background: rgba(26, 26, 46, 0.94);
  color: #fff;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
  font-size: 13px;
  line-height: 1.55;
}

.chart-tooltip-title {
  font-size: 13px;
  font-weight: 700;
  margin-bottom: 4px;
  color: #b3d4ff;
}

.chart-tooltip-total {
  font-size: 12px;
  color: #88aacc;
  margin-bottom: 6px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding-bottom: 6px;
}

.chart-tooltip-row {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 12px;
  padding: 2px 0;
}

.chart-tooltip-dot {
  width: 8px;
  height: 8px;
  border-radius: 2px;
  flex-shrink: 0;
}

.chart-tooltip-name {
  flex: 1;
  color: #aac8e8;
}

.chart-tooltip-val {
  font-weight: 700;
  color: #fff;
}

.chart-tooltip-pct {
  color: #88aacc;
  min-width: 44px;
  text-align: right;
}
</style>
