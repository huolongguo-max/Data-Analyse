<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import * as XLSX from "xlsx";

const props = defineProps({
  headers: { type: Array, default: () => [] },
  groupedHeaders: { type: Array, default: () => [] },
  rows: { type: Array, default: () => [] },
  totalRowIndex: { type: Number, default: null },
  pinFirstRow: { type: Boolean, default: false },
  disableInternalScroll: { type: Boolean, default: false },
  tableClass: { type: String, default: "wire-table" },
  cardTitle: { type: String, default: "" },
  filterLabel: { type: String, default: "" },
});

const SCROLL_THRESHOLD = 10;

const sortCol = ref(null);
const sortDir = ref(null);
const tableHeadRef = ref(null);
const stickyHeadOffset = ref(0);
const stickyHeaderTops = ref([]);
const copyFeedback = ref({ visible: false, x: 0, y: 0, text: "" });
let copyFeedbackTimer = 0;
let headResizeObserver = null;

function buildHeaderGrid() {
  if (!props.groupedHeaders.length) {
    return { grid: [], totalColumns: props.headers.length };
  }

  const grid = props.groupedHeaders.map(() => []);
  const occupied = {};
  let totalColumns = 0;

  for (let rowIndex = 0; rowIndex < props.groupedHeaders.length; rowIndex++) {
    const row = props.groupedHeaders[rowIndex];
    let col = 0;

    for (const header of row) {
      while (occupied[col] !== undefined && occupied[col] >= rowIndex) {
        col++;
      }

      const colspan = header.colspan || 1;
      const rowspan = header.rowspan || 1;

      for (let r = rowIndex; r < rowIndex + rowspan; r++) {
        for (let c = col; c < col + colspan; c++) {
          if (!grid[r]) {
            grid[r] = [];
          }
          grid[r][c] = header.label;
        }
      }

      if (rowspan > 1) {
        for (let c = col; c < col + colspan; c++) {
          occupied[c] = rowIndex + rowspan - 1;
        }
      }

      totalColumns = Math.max(totalColumns, col + colspan);
      col += colspan;
    }
  }

  return { grid, totalColumns };
}

function flatHeaders() {
  if (!props.groupedHeaders.length) {
    return props.headers;
  }

  const { grid, totalColumns } = buildHeaderGrid();
  const labels = [];

  for (let col = 0; col < totalColumns; col++) {
    const path = [];
    for (let row = 0; row < grid.length; row++) {
      const label = grid[row]?.[col];
      if (!label) {
        continue;
      }
      if (path[path.length - 1] !== label) {
        path.push(label);
      }
    }
    labels.push(path.join("-"));
  }

  return labels;
}

function toggleSort(colIndex) {
  if (colIndex === null) {
    return;
  }
  if (sortCol.value === colIndex) {
    if (sortDir.value === "asc") {
      sortDir.value = "desc";
      return;
    }
    sortCol.value = null;
    sortDir.value = null;
    return;
  }
  sortCol.value = colIndex;
  sortDir.value = "asc";
}

function sortIcon(colIndex) {
  if (sortCol.value !== colIndex || sortDir.value === null) {
    return "↕";
  }
  return sortDir.value === "asc" ? "▲" : "▼";
}

const groupedLeafMap = computed(() => {
  if (!props.groupedHeaders.length) {
    return [];
  }

  const result = [];
  const occupied = {};

  for (let rowIndex = 0; rowIndex < props.groupedHeaders.length; rowIndex++) {
    const row = props.groupedHeaders[rowIndex];
    let col = 0;
    let thIndex = 0;

    while (thIndex < row.length) {
      while (occupied[col] !== undefined && occupied[col] >= rowIndex) {
        col++;
      }

      const header = row[thIndex];
      if (!header) {
        break;
      }

      const colspan = header.colspan || 1;
      const rowspan = header.rowspan || 1;

      if (!header.colspan) {
        result.push({ rowIndex, thIndex, dataColIndex: col });
      }

      if (rowspan > 1) {
        for (let c = col; c < col + colspan; c++) {
          occupied[c] = rowIndex + rowspan - 1;
        }
      }

      col += colspan;
      thIndex++;
    }
  }

  return result;
});

function getDataColIndex(rowIndex, thIndex) {
  const entry = groupedLeafMap.value.find((item) => item.rowIndex === rowIndex && item.thIndex === thIndex);
  return entry ? entry.dataColIndex : null;
}

function cellText(cell) {
  if (typeof cell === "object" && cell !== null) {
    if (Object.hasOwn(cell, "html")) {
      return cell.html.replace(/<[^>]+>/g, "");
    }
    if (Object.hasOwn(cell, "text")) {
      return cell.text;
    }
  }
  return cell ?? "";
}

function sortValue(cell) {
  if (typeof cell === "object" && cell !== null && Object.hasOwn(cell, "sortValue")) {
    const value = Number(cell.sortValue);
    return Number.isFinite(value) ? value : null;
  }
  return null;
}

function numericVal(cell) {
  const explicitValue = sortValue(cell);
  if (explicitValue !== null) {
    return explicitValue;
  }
  const text = cellText(cell);
  const normalized = String(text)
    .trim()
    .replace(/,/g, "")
    .replace(/[−–—]/g, "-");
  if (!/^[+-]?(?:\d+\.?\d*|\.\d+)(?:[%％])?$/.test(normalized)) {
    return null;
  }
  const value = Number(normalized.replace(/[%％]/g, ""));
  return Number.isFinite(value) ? value : null;
}

const totalRow = computed(() => {
  if (props.totalRowIndex === null) {
    return null;
  }
  return props.rows[props.totalRowIndex] ?? null;
});

const pinnedTopRow = computed(() => {
  if (!props.pinFirstRow) {
    return null;
  }
  if (props.totalRowIndex === 0) {
    return null;
  }
  return props.rows[0] ?? null;
});

const dataRows = computed(() => {
  return props.rows.filter((_, index) => {
    if (props.totalRowIndex !== null && index === props.totalRowIndex) {
      return false;
    }
    if (props.pinFirstRow && index === 0) {
      return false;
    }
    return true;
  });
});

const sortedRows = computed(() => {
  const rows = [...dataRows.value];
  if (sortCol.value === null || sortDir.value === null) {
    return rows;
  }

  rows.sort((left, right) => {
    const leftNum = numericVal(left[sortCol.value]);
    const rightNum = numericVal(right[sortCol.value]);
    if (leftNum !== null || rightNum !== null) {
      if (leftNum === null) {
        return 1;
      }
      if (rightNum === null) {
        return -1;
      }
      return sortDir.value === "asc" ? leftNum - rightNum : rightNum - leftNum;
    }

    const leftText = String(cellText(left[sortCol.value]));
    const rightText = String(cellText(right[sortCol.value]));
    return sortDir.value === "asc" ? leftText.localeCompare(rightText) : rightText.localeCompare(leftText);
  });

  return rows;
});

const displayRows = computed(() => {
  const rows = [];
  if (pinnedTopRow.value) {
    rows.push(pinnedTopRow.value);
  }
  rows.push(...sortedRows.value);
  if (totalRow.value) {
    rows.push(totalRow.value);
  }
  return rows;
});

const needsScroll = computed(() => !props.disableInternalScroll && displayRows.value.length > SCROLL_THRESHOLD);
const showPinnedTopHeaderRow = computed(() => Boolean(pinnedTopRow.value && needsScroll.value));
const renderedBodyRows = computed(() => {
  if (!showPinnedTopHeaderRow.value) {
    return displayRows.value;
  }
  return displayRows.value.filter((row) => row !== pinnedTopRow.value);
});
const showHeaderBar = computed(() => Boolean(props.cardTitle || props.filterLabel));

function isHtmlCell(cell) {
  return typeof cell === "object" && cell !== null && Object.hasOwn(cell, "html");
}

function isTotalRow(row) {
  return totalRow.value && row === totalRow.value;
}

function isPinnedTopRow(row) {
  return pinnedTopRow.value && row === pinnedTopRow.value;
}

function updateStickyHeadOffset() {
  nextTick(() => {
    const rows = Array.from(tableHeadRef.value?.querySelectorAll('tr[data-header-row="true"]') || []);
    const headRect = tableHeadRef.value?.getBoundingClientRect();
    if (!headRect || !rows.length) {
      stickyHeaderTops.value = [];
      stickyHeadOffset.value = 0;
      return;
    }
    const tops = rows.map((row) => Math.round(row.getBoundingClientRect().top - headRect.top));
    stickyHeaderTops.value = tops;
    const lastRowRect = rows[rows.length - 1].getBoundingClientRect();
    stickyHeadOffset.value = Math.ceil(lastRowRect.bottom - headRect.top);
  });
}

function stickyHeaderStyle(rowIndex) {
  if (!needsScroll.value) {
    return null;
  }
  return {
    top: `${stickyHeaderTops.value[rowIndex] || 0}px`,
    zIndex: String(Math.max(2, 10 - rowIndex)),
  };
}

function buildTsvData() {
  const headers = flatHeaders();
  const lines = [headers.join("\t")];
  for (const row of displayRows.value) {
    lines.push(row.map((cell) => cellText(cell)).join("\t"));
  }
  return lines.join("\n");
}

function showCopyFeedback(event, text) {
  if (copyFeedbackTimer) {
    window.clearTimeout(copyFeedbackTimer);
    copyFeedbackTimer = 0;
  }

  copyFeedback.value = {
    visible: true,
    x: event?.clientX ?? window.innerWidth / 2,
    y: event?.clientY ?? 80,
    text,
  };

  copyFeedbackTimer = window.setTimeout(() => {
    copyFeedback.value.visible = false;
    copyFeedbackTimer = 0;
  }, 1200);
}

async function copyTable(event) {
  try {
    await navigator.clipboard.writeText(buildTsvData());
    showCopyFeedback(event, "复制成功");
  } catch {
    try {
      const textarea = document.createElement("textarea");
      textarea.value = buildTsvData();
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
      showCopyFeedback(event, "复制成功");
    } catch {
      showCopyFeedback(event, "复制失败");
    }
  }
}

function sanitizeFilenamePart(value) {
  return String(value ?? "")
    .replace(/[<>:"/\\|?*\u0000-\u001F]/g, "_")
    .trim();
}

function downloadXlsx() {
  const headers = flatHeaders();
  const data = [headers, ...displayRows.value.map((row) => row.map((cell) => cellText(cell)))];
  const sheet = XLSX.utils.aoa_to_sheet(data);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, sheet, "数据");
  const name = [props.filterLabel, props.cardTitle]
    .map((part) => sanitizeFilenamePart(part))
    .filter(Boolean)
    .join("_") || "看板";
  XLSX.writeFile(workbook, `${name}.xlsx`);
}

onBeforeUnmount(() => {
  if (copyFeedbackTimer) {
    window.clearTimeout(copyFeedbackTimer);
    copyFeedbackTimer = 0;
  }
  if (headResizeObserver) {
    headResizeObserver.disconnect();
    headResizeObserver = null;
  }
  window.removeEventListener("resize", updateStickyHeadOffset);
});

onMounted(() => {
  updateStickyHeadOffset();
  window.addEventListener("resize", updateStickyHeadOffset);
  if (typeof ResizeObserver !== "undefined" && tableHeadRef.value) {
    headResizeObserver = new ResizeObserver(() => updateStickyHeadOffset());
    headResizeObserver.observe(tableHeadRef.value);
  }
});

watch(
  () => [props.headers, props.groupedHeaders, props.rows.length, needsScroll.value],
  () => updateStickyHeadOffset(),
  { deep: true }
);
</script>

<template>
  <div class="dt-wrap">
    <div v-if="showHeaderBar" class="card-title dt-header">
      <span class="dt-title-text">{{ props.cardTitle }}</span>
      <div class="dt-toolbar">
        <button class="dt-btn" type="button" title="复制到剪贴板（可粘贴到 Excel）" @click="copyTable($event)">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path d="M4 2a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V2zm2-1a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1H6zM2 5a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1v-1H10v1H2V6h1V5H2z"/></svg>
          复制
        </button>
        <button class="dt-btn" type="button" title="下载为 xlsx" @click="downloadXlsx">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/><path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/></svg>
          下载
        </button>
      </div>
    </div>

    <slot name="before-table" />

    <teleport to="body">
      <div
        v-if="copyFeedback.visible"
        class="copy-feedback"
        :style="{ left: `${copyFeedback.x + 12}px`, top: `${copyFeedback.y - 12}px` }"
      >
        {{ copyFeedback.text }}
      </div>
    </teleport>

    <div v-if="!rows.length" class="empty-state">当前没有可展示的数据。</div>
    <div
      v-else
      :class="['table-scroll', { 'table-scroll--fixed': needsScroll, 'table-scroll--with-pinned-head': showPinnedTopHeaderRow }]"
      :style="{ '--dt-sticky-head-offset': `${stickyHeadOffset}px` }"
    >
      <table :class="tableClass">
        <thead ref="tableHeadRef">
          <template v-if="groupedHeaders.length">
            <tr v-for="(headerRow, hri) in groupedHeaders" :key="`group-${hri}`" data-header-row="true">
              <th
                v-for="(header, hi) in headerRow"
                :key="`group-${hri}-${hi}`"
                :colspan="header.colspan || 1"
                :rowspan="header.rowspan || 1"
                :class="[header.className || '', !header.colspan ? 'sortable-th' : '']"
                :style="stickyHeaderStyle(hri)"
                @click="toggleSort(getDataColIndex(hri, hi))"
              >
                {{ header.label }}
                <span v-if="!header.colspan" class="sort-icon">
                  {{ sortIcon(getDataColIndex(hri, hi)) }}
                </span>
              </th>
            </tr>
          </template>
          <tr v-else data-header-row="true">
            <th
              v-for="(header, hi) in headers"
              :key="header"
              class="sortable-th"
              :style="stickyHeaderStyle(0)"
              @click="toggleSort(hi)"
            >
              {{ header }}
              <span class="sort-icon">{{ sortIcon(hi) }}</span>
            </th>
          </tr>
          <tr v-if="showPinnedTopHeaderRow" class="thead-pinned-row">
            <th v-for="(cell, ci) in pinnedTopRow" :key="`pinned-head-${ci}`" :style="{ top: `${stickyHeadOffset}px` }">
              <span v-if="isHtmlCell(cell)" v-html="cell.html"></span>
              <span v-else>{{ cell }}</span>
            </th>
          </tr>
        </thead>
        <tbody>
            <tr
              v-for="(row, ri) in renderedBodyRows"
              :key="`${ri}-${headers.length}`"
              :class="{ 'row-total': isTotalRow(row), 'row-pinned-top': isPinnedTopRow(row) }"
            >
            <td v-for="(cell, ci) in row" :key="`${ri}-${ci}`">
              <span v-if="isHtmlCell(cell)" v-html="cell.html"></span>
              <span v-else>{{ cell }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.dt-wrap { display: flex; flex-direction: column; gap: 6px; min-width: 0; max-width: 100%; }

.dt-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 8px;
  min-width: 0;
}

.dt-title-text {
  min-width: 0;
  flex: 1;
}

.dt-toolbar {
  display: flex;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 6px;
  margin-left: auto;
  flex-shrink: 0;
  max-width: 100%;
}

.dt-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  font-size: 12px;
  color: #555;
  background: #f5f6fa;
  border: 1px solid #dde1ea;
  border-radius: 5px;
  cursor: pointer;
  transition: background 0.15s;
}

.dt-btn:hover { background: #e8ecf5; color: #1a73e8; }

.copy-feedback {
  position: fixed;
  z-index: 2200;
  transform: translateY(-50%);
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(26, 115, 232, 0.92);
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  line-height: 1;
  pointer-events: none;
  box-shadow: 0 8px 20px rgba(26, 115, 232, 0.24);
  animation: copy-feedback-pop 1.2s ease forwards;
}

@keyframes copy-feedback-pop {
  0% {
    opacity: 0;
    transform: translateY(-42%) scale(0.92);
  }

  15% {
    opacity: 1;
    transform: translateY(-56%) scale(1);
  }

  100% {
    opacity: 0;
    transform: translateY(-78%) scale(0.98);
  }
}

.table-scroll--fixed {
  max-height: 480px;
  overflow-y: auto;
  overflow-x: auto;
}

.table-scroll--fixed thead th {
  position: sticky;
  background: #f5f6fa;
}

.table-scroll--with-pinned-head thead th {
  background: #f3f4f6;
}

.table-scroll--with-pinned-head thead tr:not(.thead-pinned-row):last-child th {
  border-bottom: 0;
  box-shadow: none;
}

.row-pinned-top td {
  background: #f3f4f6 !important;
  font-weight: 700;
}

.table-scroll--fixed .thead-pinned-row th {
  position: sticky;
  top: var(--dt-sticky-head-offset, 40px);
  z-index: 8;
  background: #f3f4f6 !important;
  font-weight: 700;
  border-top: 0;
  border-bottom: 1px solid #d9dde5;
  box-shadow: none;
}

.table-scroll--fixed .row-pinned-top td {
  position: static;
  box-shadow: inset 0 -1px 0 #d9dde5;
}

.sortable-th {
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
}

.sortable-th:hover { background: #eef2fb; }

.sort-icon {
  display: inline-block;
  margin-left: 4px;
  font-size: 10px;
  color: #aaa;
  vertical-align: middle;
}
</style>
