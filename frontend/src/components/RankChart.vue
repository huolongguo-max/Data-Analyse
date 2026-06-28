<script setup>
import { computed, ref } from "vue";

const props = defineProps({
  rows: { type: Array, default: () => [] },
  visibleCount: { type: Number, default: 15 },
});

const tooltip = ref({
  visible: false,
  x: 0,
  y: 0,
  name: "",
  primary: null,
  secondary: null,
  totalLabel: "合计",
  total: "",
});

const seriesMode = ref("all");

const activeSeries = computed(() =>
  seriesMode.value === "all" ? ["primary", "secondary"] : [seriesMode.value]
);

const legendItems = computed(() => [
  { key: "primary", label: props.rows[0]?.primaryLabel || "本期" },
  { key: "secondary", label: props.rows[0]?.secondaryLabel || "上期" },
  { key: "all", label: "全部" },
]);

function seriesValue(row, key) {
  return key === "primary" ? Number(row.primaryValue || 0) : Number(row.secondaryValue || 0);
}

function displayValue(row) {
  return activeSeries.value.reduce((sum, key) => sum + seriesValue(row, key), 0);
}

function displayText(row) {
  if (seriesMode.value === "primary") {
    return row.primaryText;
  }
  if (seriesMode.value === "secondary") {
    return row.secondaryText;
  }
  return row.totalText;
}

const sortedRows = computed(() =>
  [...props.rows].sort((left, right) => displayValue(right) - displayValue(left))
);

const maxDisplayTotal = computed(() => Math.max(1, ...sortedRows.value.map((row) => displayValue(row))));
const positiveDisplayValues = computed(() =>
  sortedRows.value
    .map((row) => displayValue(row))
    .filter((value) => value > 0)
);
const minDisplayTotal = computed(() =>
  positiveDisplayValues.value.length ? Math.min(...positiveDisplayValues.value) : 0
);

const needsScroll = computed(() => sortedRows.value.length > props.visibleCount);
const chartVars = computed(() => ({ "--rank-visible-count": String(props.visibleCount) }));

function barWidth(row) {
  const value = displayValue(row);
  if (value <= 0) {
    return "0%";
  }
  if (!positiveDisplayValues.value.length) {
    return "0%";
  }
  if (maxDisplayTotal.value <= minDisplayTotal.value) {
    return "100%";
  }
  const minRatio = 0.22;
  const normalized = (value - minDisplayTotal.value) / (maxDisplayTotal.value - minDisplayTotal.value);
  return `${(minRatio + normalized * (1 - minRatio)) * 100}%`;
}

function segmentWidth(row, key) {
  const total = displayValue(row);
  if (!total) {
    return "0%";
  }
  return `${(seriesValue(row, key) / total) * 100}%`;
}

function setSeriesMode(nextMode) {
  if (nextMode === "all") {
    seriesMode.value = "all";
    return;
  }
  seriesMode.value = seriesMode.value === nextMode ? "all" : nextMode;
}

function showTip(event, row) {
  const rect = event.currentTarget.closest(".rank-chart").getBoundingClientRect();
  tooltip.value = {
    visible: true,
    x: event.clientX - rect.left + 14,
    y: event.clientY - rect.top - 8,
    name: row.name,
    primary: { label: row.primaryLabel || "本期", value: row.primaryValue, text: row.primaryText },
    secondary: { label: row.secondaryLabel || "上期", value: row.secondaryValue, text: row.secondaryText },
    totalLabel:
      seriesMode.value === "primary"
        ? row.primaryLabel || "本期"
        : seriesMode.value === "secondary"
          ? row.secondaryLabel || "上期"
          : "合计",
    total: displayText(row),
  };
}

function moveTip(event) {
  if (!tooltip.value.visible) {
    return;
  }
  const rect = event.currentTarget.closest(".rank-chart").getBoundingClientRect();
  tooltip.value.x = event.clientX - rect.left + 14;
  tooltip.value.y = event.clientY - rect.top - 8;
}

function hideTip() {
  tooltip.value.visible = false;
}
</script>

<template>
  <div v-if="!rows.length" class="empty-state">当前没有可展示的数据。</div>
  <div v-else class="rank-chart" :style="chartVars">
    <div class="rank-legend">
      <button
        v-for="item in legendItems"
        :key="item.key"
        type="button"
        class="rank-legend-toggle"
        :class="{ active: seriesMode === item.key }"
        @click="setSeriesMode(item.key)"
      >
        <span v-if="item.key === 'all'" class="rank-legend-dot-pair" aria-hidden="true">
          <span class="rank-legend-dot primary-dot"></span>
          <span class="rank-legend-dot secondary-dot"></span>
        </span>
        <span v-else class="rank-legend-dot" :class="item.key === 'primary' ? 'primary-dot' : 'secondary-dot'" aria-hidden="true"></span>
        {{ item.label }}
      </button>
    </div>

    <div class="rank-chart-body" :class="{ 'rank-chart-body--scroll': needsScroll }">
      <div
        v-for="row in sortedRows"
        :key="row.name"
        class="rank-row"
        @mouseenter="(event) => showTip(event, row)"
        @mousemove="moveTip"
        @mouseleave="hideTip"
      >
        <div class="rank-name" :title="row.name">{{ row.name }}</div>
        <div class="rank-track">
          <div class="rank-track-fill" :style="{ width: barWidth(row) }">
            <div
              v-if="activeSeries.includes('primary')"
              class="rank-segment primary-bar"
              :style="{ width: segmentWidth(row, 'primary') }"
            ></div>
            <div
              v-if="activeSeries.includes('secondary')"
              class="rank-segment secondary-bar"
              :style="{ width: segmentWidth(row, 'secondary') }"
            ></div>
          </div>
        </div>
        <div class="rank-total">{{ displayText(row) }}</div>
      </div>
    </div>

    <div
      v-if="tooltip.visible"
      class="chart-tooltip"
      :style="{ left: `${tooltip.x}px`, top: `${tooltip.y}px` }"
    >
      <div class="chart-tooltip-title">{{ tooltip.name }}</div>
      <div class="chart-tooltip-row">
        <span class="chart-tooltip-dot" style="background:#1a73e8"></span>
        <span class="chart-tooltip-name">{{ tooltip.primary?.label }}</span>
        <span class="chart-tooltip-val">{{ tooltip.primary?.text }}</span>
      </div>
      <div class="chart-tooltip-row">
        <span class="chart-tooltip-dot" style="background:#ff9f43"></span>
        <span class="chart-tooltip-name">{{ tooltip.secondary?.label }}</span>
        <span class="chart-tooltip-val">{{ tooltip.secondary?.text }}</span>
      </div>
      <div class="chart-tooltip-total">{{ tooltip.totalLabel }}：{{ tooltip.total }}</div>
    </div>
  </div>
</template>

<style scoped>
.rank-chart {
  position: relative;
  display: grid;
  gap: 14px;
  --rank-visible-count: 15;
  --rank-row-height: 28px;
  --rank-row-gap: 8px;
}

.rank-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.rank-legend-toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border: 1px solid #dde3ee;
  border-radius: 999px;
  background: #fff;
  color: #667085;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.18s ease;
}

.rank-legend-toggle:hover {
  border-color: #c7d2e5;
  background: #f8fbff;
}

.rank-legend-toggle.active {
  border-color: #c7d8fb;
  background: #eef4ff;
  color: #2854a6;
}

.rank-legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 3px;
  flex-shrink: 0;
}

.rank-legend-dot-pair {
  display: inline-flex;
  gap: 4px;
  align-items: center;
  flex-shrink: 0;
}

.primary-dot {
  background: linear-gradient(90deg, #4fc3f7, #1a73e8);
}

.secondary-dot {
  background: linear-gradient(90deg, #ffcc80, #ff9800);
}

.rank-chart-body {
  display: grid;
  gap: var(--rank-row-gap);
}

.rank-chart-body--scroll {
  max-height: calc(
    var(--rank-visible-count) * var(--rank-row-height) +
    (var(--rank-visible-count) - 1) * var(--rank-row-gap)
  );
  overflow-y: auto;
  padding-right: 4px;
}

.rank-chart-body--scroll::-webkit-scrollbar {
  width: 8px;
}

.rank-chart-body--scroll::-webkit-scrollbar-thumb {
  border-radius: 999px;
  background: #d0d5dd;
}

.rank-row {
  display: grid;
  grid-template-columns: minmax(72px, 100px) minmax(0, 1fr) minmax(56px, 88px);
  align-items: center;
  gap: 12px;
  min-height: var(--rank-row-height);
  cursor: default;
}

.rank-name {
  font-size: 12px;
  font-weight: 500;
  color: #555;
  text-align: right;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.rank-track {
  display: flex;
  align-items: center;
  min-height: 14px;
  border-radius: 0;
  background: transparent !important;
  overflow: visible;
}

.rank-track-fill {
  display: flex;
  align-items: stretch;
  height: 14px;
  overflow: hidden;
  border-radius: 999px;
  background: transparent;
  transition: width 0.35s ease;
}

.rank-segment {
  height: 100%;
  min-width: 0;
  transition: width 0.35s ease;
}

.primary-bar {
  background: linear-gradient(90deg, #4fc3f7, #1a73e8);
}

.secondary-bar {
  background: linear-gradient(90deg, #ffcc80, #ff9800);
}

.rank-total {
  min-width: 0;
  font-size: 12px;
  font-weight: 600;
  color: #444;
  text-align: right;
  white-space: nowrap;
}

.chart-tooltip {
  position: absolute;
  z-index: 100;
  pointer-events: none;
  min-width: 190px;
  padding: 10px 14px;
  border-radius: 10px;
  background: rgba(26, 26, 46, 0.94);
  color: #fff;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
  font-size: 13px;
  line-height: 1.55;
}

.chart-tooltip-title {
  margin-bottom: 6px;
  color: #b3d4ff;
  font-size: 13px;
  font-weight: 700;
}

.chart-tooltip-total {
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  color: #88aacc;
  font-size: 12px;
}

.chart-tooltip-row {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 2px 0;
  font-size: 12px;
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
  color: #fff;
  font-weight: 700;
}
</style>
