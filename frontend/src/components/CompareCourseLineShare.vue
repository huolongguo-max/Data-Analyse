<script setup>
import { computed, ref } from "vue";

const props = defineProps({
  groups: { type: Array, default: () => [] },
});

const COLOR_STOPS = [
  ["#81D4FA", "#4FC3F7"],
  ["#FFCC80", "#FFB74D"],
  ["#A5D6A7", "#81C784"],
  ["#F8BBD0", "#EC4899"],
  ["#C4B5FD", "#8B5CF6"],
  ["#B2DFDB", "#26A69A"],
  ["#FFE082", "#F59E0B"],
  ["#90CAF9", "#2563EB"],
];

const tooltip = ref({
  visible: false,
  x: 0,
  y: 0,
  courseLine: "",
  groupTitle: "",
  metricLabel: "",
  period: "",
  value: "",
  pct: "",
});

const legendItems = computed(() => {
  const source = props.groups[0]?.metrics[0]?.current || [];
  return source.map((segment, index) => ({
    label: segment.label,
    style: gradientStyle(index),
  }));
});

function gradientStyle(index) {
  const [start, end] = COLOR_STOPS[index % COLOR_STOPS.length];
  return {
    background: `linear-gradient(180deg, ${start} 0%, ${end} 100%)`,
  };
}

function segmentStyle(index, segment) {
  return {
    ...gradientStyle(index),
    height: `${Math.max(Number(segment?.pct || 0) * 100, 0)}%`,
    minHeight: Number(segment?.rawValue || 0) > 0 ? "2px" : "0",
  };
}

function formatPercent(value) {
  return `${(Number(value || 0) * 100).toFixed(0)}%`;
}

function showTip(event, payload) {
  const rect = event.currentTarget.closest(".compare-course-share").getBoundingClientRect();
  tooltip.value = {
    visible: true,
    x: event.clientX - rect.left + 14,
    y: event.clientY - rect.top - 10,
    ...payload,
  };
}

function moveTip(event) {
  if (!tooltip.value.visible) {
    return;
  }
  const rect = event.currentTarget.closest(".compare-course-share").getBoundingClientRect();
  tooltip.value.x = event.clientX - rect.left + 14;
  tooltip.value.y = event.clientY - rect.top - 10;
}

function hideTip() {
  tooltip.value.visible = false;
}
</script>

<template>
  <div v-if="!groups.length" class="empty-state">当前没有可展示的数据。</div>
  <div v-else class="compare-course-share">
    <div class="bar-legend compare-course-share-legend">
      <span v-for="item in legendItems" :key="item.label" class="compare-course-share-legend-item">
        <span class="legend-dot compare-course-share-legend-dot" :style="item.style"></span>
        {{ item.label }}
      </span>
    </div>

    <div class="compare-course-share-layout">
      <section
        v-for="group in groups"
        :key="group.key"
        class="compare-course-share-group"
        :class="`compare-course-share-group--${group.key}`"
        >
          <header class="compare-course-share-group-head">
            <div class="compare-course-share-group-title">{{ group.title }}</div>
          </header>

        <div class="compare-course-share-metrics">
          <div v-for="metric in group.metrics" :key="`${group.key}-${metric.key}`" class="compare-course-share-metric-card">
            <div class="compare-course-share-bars">
              <div class="compare-course-share-period-block">
                <div class="st-bar">
                  <div
                    v-for="(segment, index) in metric.current"
                    :key="`${metric.key}-current-${segment.label}`"
                    class="st-seg compare-course-share-segment"
                    :style="segmentStyle(index, segment)"
                    @mouseenter="showTip($event, { courseLine: segment.label, groupTitle: group.title, metricLabel: metric.label, period: '本期', value: segment.display, pct: formatPercent(segment.pct) })"
                    @mousemove="moveTip"
                    @mouseleave="hideTip"
                  ></div>
                </div>
                <div class="st-labels"><span>本期</span></div>
              </div>

              <div class="compare-course-share-period-block">
                <div class="st-bar">
                  <div
                    v-for="(segment, index) in metric.previous"
                    :key="`${metric.key}-previous-${segment.label}`"
                    class="st-seg compare-course-share-segment"
                    :style="segmentStyle(index, segment)"
                    @mouseenter="showTip($event, { courseLine: segment.label, groupTitle: group.title, metricLabel: metric.label, period: '上期', value: segment.display, pct: formatPercent(segment.pct) })"
                    @mousemove="moveTip"
                    @mouseleave="hideTip"
                  ></div>
                </div>
                <div class="st-labels"><span>上期</span></div>
              </div>
            </div>

            <div class="st-metric-name">{{ metric.label }}</div>
          </div>
        </div>
      </section>
    </div>

    <div
      v-if="tooltip.visible"
      class="chart-tooltip"
      :style="{ left: `${tooltip.x}px`, top: `${tooltip.y}px` }"
    >
      <div class="chart-tooltip-title">{{ tooltip.courseLine }}</div>
      <div class="chart-tooltip-row">
        <span class="chart-tooltip-name">板块</span>
        <span class="chart-tooltip-val">{{ tooltip.groupTitle }}</span>
      </div>
      <div class="chart-tooltip-row">
        <span class="chart-tooltip-name">指标</span>
        <span class="chart-tooltip-val">{{ tooltip.metricLabel }}</span>
      </div>
      <div class="chart-tooltip-row">
        <span class="chart-tooltip-name">{{ tooltip.period }}</span>
        <span class="chart-tooltip-val">{{ tooltip.value }}</span>
      </div>
      <div class="chart-tooltip-row">
        <span class="chart-tooltip-name">占比</span>
        <span class="chart-tooltip-val">{{ tooltip.pct }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.compare-course-share {
  position: relative;
}

.bar-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 24px;
  justify-content: center;
  margin-bottom: 14px;
  font-size: 12px;
  color: #777;
  font-weight: 500;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  display: inline-block;
  vertical-align: middle;
}

.compare-course-share-legend-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #777;
  font-weight: 500;
}

.compare-course-share-legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  flex-shrink: 0;
  margin-right: 0;
}

.compare-course-share-layout {
  display: flex;
  gap: 32px;
}

.compare-course-share-group {
  border-radius: 8px;
  padding: 16px;
  background: #fff;
  flex: 1;
}

.compare-course-share-group--reserve {
  border: 1px solid #dbeafe;
}

.compare-course-share-group--performance {
  border: 1px solid #ffedd5;
}

.compare-course-share-group-head {
  margin-bottom: 12px;
}

.compare-course-share-group-title {
  padding-left: 10px;
  font-size: 15px;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 2px;
}

.compare-course-share-group--reserve .compare-course-share-group-title {
  border-left: 3px solid #4FC3F7;
}

.compare-course-share-group--performance .compare-course-share-group-title {
  border-left: 3px solid #FFB74D;
}

.compare-course-share-metrics {
  display: flex;
  gap: 24px;
  justify-content: space-between;
}

.compare-course-share-metric-card {
  min-width: 90px;
  flex: 1;
}

.compare-course-share-bars {
  display: flex;
  gap: 10px;
  justify-content: center;
}

.compare-course-share-period-block {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.st-bar {
  width: 44px;
  height: 150px;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  border-radius: 5px;
  overflow: hidden;
  background: #f0f2f5;
}

.compare-course-share-segment {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: default;
  transition: filter 0.18s ease;
}

.compare-course-share-segment:hover {
  filter: brightness(1.08);
}

.st-labels {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 8px;
}

.st-labels span {
  font-size: 11px;
  color: #444;
  width: 48px;
  text-align: center;
  border: 1px solid #d0d5dd;
  border-radius: 4px;
  padding: 3px 0;
  background: #f7f8fa;
  font-weight: 500;
}

.st-metric-name {
  font-size: 13px;
  color: #1a1a2e;
  font-weight: 700;
  margin-top: 8px;
  text-align: center;
}

.chart-tooltip {
  position: absolute;
  z-index: 100;
  pointer-events: none;
  min-width: 210px;
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
  margin-bottom: 6px;
  color: #b3d4ff;
}

.chart-tooltip-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  font-size: 12px;
  padding: 2px 0;
}

.chart-tooltip-name {
  color: #aac8e8;
}

.chart-tooltip-val {
  font-weight: 700;
  color: #fff;
  text-align: right;
}

@media (max-width: 1100px) {
  .compare-course-share-layout {
    flex-direction: column;
    gap: 16px;
  }
}

@media (max-width: 760px) {
  .compare-course-share-metrics {
    flex-wrap: wrap;
    justify-content: center;
    gap: 18px;
  }

  .compare-course-share-metric-card {
    min-width: 110px;
    flex: 0 0 calc(50% - 12px);
  }
}
</style>
