<script setup>
import { ref } from "vue";

const props = defineProps({
  current: { type: Array, default: () => [] },
  previous: { type: Array, default: () => [] },
});

function totalValue(items) {
  return items.reduce((sum, item) => sum + Number(item.value || 0), 0);
}

function fmtNum(n) {
  return Number(n || 0).toLocaleString("zh-CN", { maximumFractionDigits: 0 });
}

const tooltip = ref({ visible: false, x: 0, y: 0, seg: null });

function showTip(e, seg) {
  const rect = e.currentTarget.closest(".share-columns").getBoundingClientRect();
  tooltip.value = {
    visible: true,
    x: e.clientX - rect.left + 14,
    y: e.clientY - rect.top - 8,
    seg,
  };
}

function moveTip(e) {
  if (!tooltip.value.visible) return;
  const rect = e.currentTarget.closest(".share-columns").getBoundingClientRect();
  tooltip.value.x = e.clientX - rect.left + 14;
  tooltip.value.y = e.clientY - rect.top - 8;
}

function hideTip() {
  tooltip.value.visible = false;
}

const COLORS = ["#1a73e8", "#ff9f43", "#43a047", "#ec4899", "#7c3aed"];
</script>

<template>
  <div v-if="!current.length && !previous.length" class="empty-state">当前没有可展示的数据。</div>
  <div v-else class="share-columns" style="position:relative">
    <!-- 图例 -->
    <div class="share-legend" v-if="current.length">
      <span v-for="(seg, idx) in current" :key="seg.label" class="share-legend-item">
        <span class="share-legend-dot" :style="{ background: COLORS[idx % 5] }"></span>
        {{ seg.label }}
      </span>
    </div>

    <div class="share-bars-row">
      <!-- 本期 -->
      <div class="share-card">
        <h4 class="share-title">本期</h4>
        <div class="share-column-wrap">
          <div class="share-column">
            <div
              v-for="(seg, idx) in current"
              :key="`c-${seg.label}`"
              class="share-seg"
              :style="{
                flex: Math.max(Number(seg.pct) * 100, 3),
                background: COLORS[idx % 5],
              }"
              @mouseenter="(e) => showTip(e, { ...seg, period: '本期' })"
              @mousemove="moveTip"
              @mouseleave="hideTip"
            ></div>
          </div>
          <div class="share-caption">总计 {{ fmtNum(totalValue(current)) }}</div>
        </div>
      </div>

      <!-- 上期 -->
      <div class="share-card">
        <h4 class="share-title">上期</h4>
        <div class="share-column-wrap">
          <div class="share-column">
            <div
              v-for="(seg, idx) in previous"
              :key="`p-${seg.label}`"
              class="share-seg"
              :style="{
                flex: Math.max(Number(seg.pct) * 100, 3),
                background: COLORS[idx % 5],
              }"
              @mouseenter="(e) => showTip(e, { ...seg, period: '上期' })"
              @mousemove="moveTip"
              @mouseleave="hideTip"
            ></div>
          </div>
          <div class="share-caption">总计 {{ fmtNum(totalValue(previous)) }}</div>
        </div>
      </div>
    </div>

    <!-- Tooltip -->
    <div
      v-if="tooltip.visible && tooltip.seg"
      class="chart-tooltip"
      :style="{ left: tooltip.x + 'px', top: tooltip.y + 'px' }"
    >
      <div class="chart-tooltip-title">{{ tooltip.seg.label }}</div>
      <div class="chart-tooltip-row">
        <span class="chart-tooltip-name">{{ tooltip.seg.period }}</span>
        <span class="chart-tooltip-val">{{ fmtNum(tooltip.seg.value) }}</span>
      </div>
      <div class="chart-tooltip-row">
        <span class="chart-tooltip-name">占比</span>
        <span class="chart-tooltip-val">{{ tooltip.seg.display }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.share-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 20px;
  margin-bottom: 12px;
}
.share-legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #777;
  font-weight: 500;
}
.share-legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 3px;
  flex-shrink: 0;
}
.share-bars-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}
.share-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.share-title {
  margin: 0;
  color: #1a1a2e;
  font-size: 13px;
  font-weight: 600;
}
.share-column-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
.share-column {
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 280px;
  height: 240px;
  overflow: hidden;
  border-radius: 8px;
  background: #f0f2f5;
}
.share-seg {
  cursor: default;
  transition: filter 0.15s ease;
  min-height: 6px;
}
.share-seg:hover { filter: brightness(1.1); }
.share-caption {
  color: #888;
  font-size: 12px;
  font-weight: 500;
  text-align: center;
}

/* Tooltip */
.chart-tooltip {
  position: absolute;
  z-index: 100;
  pointer-events: none;
  min-width: 170px;
  padding: 10px 14px;
  border-radius: 10px;
  background: rgba(26, 26, 46, 0.94);
  color: #fff;
  box-shadow: 0 4px 16px rgba(0,0,0,0.2);
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
  gap: 12px;
  font-size: 12px;
  padding: 2px 0;
}
.chart-tooltip-name { color: #aac8e8; }
.chart-tooltip-val { font-weight: 700; color: #fff; }
</style>
