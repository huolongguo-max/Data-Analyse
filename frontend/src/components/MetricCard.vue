<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: String, required: true },
  meta: { type: Array, default: () => [] },
  rateText: { type: String, default: "" },
  targetText: { type: String, default: "" },
  progress: { type: Number, default: null },
  accent: { type: Boolean, default: false },
});
</script>

<template>
  <article class="metric-card" :class="accent ? 'highlight-orange' : 'highlight'">
    <div class="metric-label">{{ label }}</div>
    <div class="metric-value">{{ value }}</div>
    <div class="metric-sub">
      <div v-for="item in meta" :key="item.label" class="metric-sub-item">
        {{ item.label }} <span>{{ item.value }}</span>
      </div>
    </div>
    <div v-if="progress !== null" class="progress-wrap">
      <div class="progress-bar">
        <div class="progress-fill" :class="accent ? 'orange' : 'blue'" :style="{ width: `${Math.max(0, Math.min(100, progress * 100))}%` }"></div>
      </div>
      <div class="progress-info">
        <span class="progress-info-rate">{{ rateText }}</span>
        <span class="progress-info-target">{{ targetText }}</span>
      </div>
    </div>
    <div v-else class="overview-spacer"></div>
  </article>
</template>
