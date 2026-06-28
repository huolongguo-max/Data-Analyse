<script setup>
import { computed, reactive, ref } from "vue";

const props = defineProps({
  visible: { type: Boolean, default: false },
});
const emit = defineEmits(["close"]);

const users = ref([]);
const loading = ref(false);
const errorMsg = ref("");
const successMsg = ref("");

// form state
const showCreateForm = ref(false);
const editingUser = ref(null); // user object being edited

const form = reactive({
  username: "",
  password: "",
  permissions: defaultPermissions(),
});

function defaultPermissions() {
  return {
    single: {
      enabled: false,
      tabs: [],
      allow_export: false,
    },
    compare: {
      enabled: false,
      tabs: [],
      allow_export: false,
    },
  };
}

const SINGLE_TABS = [
  { key: "overview", label: "总览与课线" },
  { key: "area", label: "片区" },
  { key: "region", label: "地区" },
  { key: "bd", label: "BD" },
];
const COMPARE_TABS = [
  { key: "overview", label: "总览与课线" },
  { key: "area", label: "片区" },
  { key: "region", label: "地区" },
  { key: "bd", label: "BD" },
];

function token() {
  return localStorage.getItem("auth_token") || "";
}

async function apiFetch(path, options = {}) {
  const res = await fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token()}`,
      ...(options.headers || {}),
    },
  });
  const body = await res.json();
  if (!res.ok) {
    const raw = body.detail || body.message;
    const msg = !raw ? "请求失败"
      : typeof raw === "string" ? raw
      : Array.isArray(raw) ? raw.map((e) => e?.msg || JSON.stringify(e)).join("; ")
      : JSON.stringify(raw);
    throw new Error(msg);
  }
  return body.data;
}

async function loadUsers() {
  loading.value = true;
  errorMsg.value = "";
  try {
    users.value = await apiFetch("/api/users");
  } catch (e) {
    errorMsg.value = e.message;
  } finally {
    loading.value = false;
  }
}

function openCreate() {
  editingUser.value = null;
  form.username = "";
  form.password = "";
  form.permissions = defaultPermissions();
  showCreateForm.value = true;
}

function openEdit(user) {
  editingUser.value = user;
  form.username = user.username;
  form.password = "";
  // deep copy permissions with defaults
  const p = user.permissions || {};
  form.permissions = {
    single: {
      enabled: !!(p.single?.enabled),
      tabs: [...(p.single?.tabs || [])],
      allow_export: !!(p.single?.allow_export),
    },
    compare: {
      enabled: !!(p.compare?.enabled),
      tabs: [...(p.compare?.tabs || [])],
      allow_export: !!(p.compare?.allow_export),
    },
  };
  showCreateForm.value = true;
}

function cancelForm() {
  showCreateForm.value = false;
  editingUser.value = null;
}

function toggleTab(module, tabKey) {
  const tabs = form.permissions[module].tabs;
  const idx = tabs.indexOf(tabKey);
  if (idx === -1) tabs.push(tabKey);
  else tabs.splice(idx, 1);
}

function onModuleToggle(module) {
  if (!form.permissions[module].enabled) {
    form.permissions[module].tabs = [];
    form.permissions[module].allow_export = false;
  }
}

async function submitForm() {
  errorMsg.value = "";
  successMsg.value = "";
  try {
    if (editingUser.value) {
      const body = { permissions: form.permissions };
      if (form.password) body.password = form.password;
      await apiFetch(`/api/users/${editingUser.value.id}`, {
        method: "PUT",
        body: JSON.stringify(body),
      });
      successMsg.value = "账号已更新";
    } else {
      if (!form.username || !form.password) {
        errorMsg.value = "账号和密码不能为空";
        return;
      }
      await apiFetch("/api/users", {
        method: "POST",
        body: JSON.stringify({
          username: form.username,
          password: form.password,
          permissions: form.permissions,
        }),
      });
      successMsg.value = "账号已创建";
    }
    await loadUsers();
    cancelForm();
  } catch (e) {
    errorMsg.value = e.message;
  }
}

async function toggleActive(user) {
  try {
    await apiFetch(`/api/users/${user.id}`, {
      method: "PUT",
      body: JSON.stringify({ is_active: !user.is_active }),
    });
    await loadUsers();
  } catch (e) {
    errorMsg.value = e.message;
  }
}

async function deleteUser(user) {
  if (!confirm(`确认删除账号「${user.username}」？`)) return;
  try {
    await apiFetch(`/api/users/${user.id}`, { method: "DELETE" });
    successMsg.value = "已删除";
    await loadUsers();
  } catch (e) {
    errorMsg.value = e.message;
  }
}

// watch visible to load
import { watch } from "vue";
watch(() => props.visible, (v) => {
  if (v) {
    loadUsers();
    successMsg.value = "";
    errorMsg.value = "";
    showCreateForm.value = false;
  }
});
</script>

<template>
  <teleport to="body">
    <div v-if="visible" class="perm-overlay" @click.self="emit('close')">
      <div class="perm-panel">
        <div class="perm-header">
          <span class="perm-title">权限管理</span>
          <button class="perm-close" @click="emit('close')">✕</button>
        </div>

        <div v-if="errorMsg" class="perm-msg error">{{ errorMsg }}</div>
        <div v-if="successMsg" class="perm-msg success">{{ successMsg }}</div>

        <!-- 用户列表 -->
        <template v-if="!showCreateForm">
          <div class="perm-actions">
            <button class="perm-btn primary" @click="openCreate">+ 新建账号</button>
          </div>

          <div v-if="loading" class="perm-empty">加载中...</div>
          <div v-else-if="!users.length" class="perm-empty">暂无查看者账号</div>
          <div v-else class="perm-user-list">
            <div v-for="user in users" :key="user.id" class="perm-user-row">
              <div class="perm-user-info">
                <span class="perm-username">{{ user.username }}</span>
                <span class="perm-tag" :class="user.is_active ? 'active' : 'inactive'">
                  {{ user.is_active ? "启用" : "禁用" }}
                </span>
                <span class="perm-modules">
                  {{ [user.permissions?.single?.enabled && "本期", user.permissions?.compare?.enabled && "对比"].filter(Boolean).join(" / ") || "无权限" }}
                  <span v-if="user.permissions?.single?.allow_export || user.permissions?.compare?.allow_export" class="perm-export-tag">可下载</span>
                </span>
              </div>
              <div class="perm-user-btns">
                <button class="perm-btn sm" @click="openEdit(user)">编辑</button>
                <button class="perm-btn sm warn" @click="toggleActive(user)">{{ user.is_active ? "禁用" : "启用" }}</button>
                <button class="perm-btn sm danger" @click="deleteUser(user)">删除</button>
              </div>
            </div>
          </div>
        </template>

        <!-- 创建/编辑表单 -->
        <template v-else>
          <div class="perm-form-title">{{ editingUser ? `编辑：${editingUser.username}` : "新建查看者账号" }}</div>

          <div class="perm-form">
            <div v-if="!editingUser" class="perm-form-row">
              <label>账号</label>
              <input v-model="form.username" type="text" placeholder="登录账号" />
            </div>
            <div class="perm-form-row">
              <label>{{ editingUser ? "新密码（留空不修改）" : "密码" }}</label>
              <input v-model="form.password" type="password" :placeholder="editingUser ? '留空不修改' : '登录密码'" />
            </div>

            <!-- 权限设置 -->
            <div class="perm-section-title">权限设置</div>

            <!-- 本期看板 -->
            <div class="perm-module">
              <label class="perm-module-check">
                <input type="checkbox" v-model="form.permissions.single.enabled" @change="onModuleToggle('single')" />
                <span class="perm-module-name">本期看板</span>
              </label>
              <template v-if="form.permissions.single.enabled">
                <div class="perm-tabs">
                  <label v-for="tab in SINGLE_TABS" :key="tab.key" class="perm-tab-check">
                    <input type="checkbox"
                      :checked="form.permissions.single.tabs.includes(tab.key)"
                      @change="toggleTab('single', tab.key)" />
                    {{ tab.label }}
                  </label>
                </div>
                <label class="perm-export-check">
                  <input type="checkbox" v-model="form.permissions.single.allow_export" />
                  允许复制 / 下载
                </label>
              </template>
            </div>

            <!-- 两期对比看板 -->
            <div class="perm-module">
              <label class="perm-module-check">
                <input type="checkbox" v-model="form.permissions.compare.enabled" @change="onModuleToggle('compare')" />
                <span class="perm-module-name">两期对比看板</span>
              </label>
              <template v-if="form.permissions.compare.enabled">
                <div class="perm-tabs">
                  <label v-for="tab in COMPARE_TABS" :key="tab.key" class="perm-tab-check">
                    <input type="checkbox"
                      :checked="form.permissions.compare.tabs.includes(tab.key)"
                      @change="toggleTab('compare', tab.key)" />
                    {{ tab.label }}
                  </label>
                </div>
                <label class="perm-export-check">
                  <input type="checkbox" v-model="form.permissions.compare.allow_export" />
                  允许复制 / 下载
                </label>
              </template>
            </div>

            <div class="perm-form-actions">
              <button class="perm-btn primary" @click="submitForm">确定</button>
              <button class="perm-btn" @click="cancelForm">取消</button>
            </div>
          </div>
        </template>
      </div>
    </div>
  </teleport>
</template>

<style scoped>
.perm-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(0,0,0,0.45);
  display: flex;
  align-items: flex-start;
  justify-content: flex-end;
}

.perm-panel {
  width: 420px;
  max-width: 100vw;
  height: 100vh;
  background: #fff;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  box-shadow: -4px 0 24px rgba(0,0,0,0.15);
}

.perm-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 16px;
  border-bottom: 1px solid #eef0f4;
  position: sticky;
  top: 0;
  background: #fff;
  z-index: 1;
}

.perm-title {
  font-size: 16px;
  font-weight: 700;
  color: #1a1a2e;
}

.perm-close {
  background: none;
  border: none;
  font-size: 16px;
  color: #888;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 4px;
}
.perm-close:hover { background: #f0f2f5; }

.perm-msg {
  margin: 12px 24px 0;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 13px;
}
.perm-msg.error { background: #fce8e6; color: #d93025; }
.perm-msg.success { background: #e6f4ea; color: #1e7e34; }

.perm-actions {
  padding: 16px 24px 8px;
}

.perm-empty {
  padding: 32px 24px;
  color: #aaa;
  font-size: 13px;
  text-align: center;
}

.perm-user-list {
  display: flex;
  flex-direction: column;
  padding: 0 24px 24px;
  gap: 10px;
}

.perm-user-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border: 1px solid #eef0f4;
  border-radius: 8px;
  background: #fafbfd;
}

.perm-user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  flex: 1;
  min-width: 0;
}

.perm-username {
  font-size: 14px;
  font-weight: 600;
  color: #1a1a2e;
}

.perm-tag {
  font-size: 11px;
  padding: 2px 7px;
  border-radius: 10px;
  font-weight: 600;
}
.perm-tag.active { background: #e6f4ea; color: #1e7e34; }
.perm-tag.inactive { background: #f5f5f5; color: #999; }

.perm-modules {
  font-size: 12px;
  color: #666;
}

.perm-export-tag {
  display: inline-block;
  margin-left: 4px;
  font-size: 11px;
  padding: 1px 5px;
  border-radius: 4px;
  background: #e8f0fe;
  color: #1a73e8;
  font-weight: 600;
}

.perm-user-btns {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

/* Buttons */
.perm-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 6px 14px;
  border: 1px solid #dde1ea;
  border-radius: 6px;
  background: #fff;
  font-size: 13px;
  color: #444;
  cursor: pointer;
  transition: background 0.12s;
}
.perm-btn:hover { background: #f5f7fb; }
.perm-btn.primary { background: #1a73e8; color: #fff; border-color: #1a73e8; }
.perm-btn.primary:hover { background: #1557b0; }
.perm-btn.warn { color: #d97706; border-color: #d97706; }
.perm-btn.warn:hover { background: #fffbeb; }
.perm-btn.danger { color: #d93025; border-color: #d93025; }
.perm-btn.danger:hover { background: #fce8e6; }
.perm-btn.sm { padding: 4px 10px; font-size: 12px; }

/* Form */
.perm-form-title {
  padding: 16px 24px 4px;
  font-size: 14px;
  font-weight: 700;
  color: #1a1a2e;
}

.perm-form {
  padding: 8px 24px 32px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.perm-form-row {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.perm-form-row label {
  font-size: 13px;
  font-weight: 600;
  color: #555;
}

.perm-form-row input {
  padding: 8px 10px;
  border: 1px solid #dde1ea;
  border-radius: 6px;
  font-size: 13px;
  outline: none;
}
.perm-form-row input:focus { border-color: #1a73e8; box-shadow: 0 0 0 2px rgba(26,115,232,0.1); }

.perm-section-title {
  font-size: 13px;
  font-weight: 700;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding-top: 4px;
  border-top: 1px solid #f0f2f5;
}

.perm-module {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  border: 1px solid #eef0f4;
  border-radius: 8px;
  background: #fafbfd;
}

.perm-module-check {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
}

.perm-module-name {
  font-weight: 600;
  color: #1a1a2e;
}

.perm-tabs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
  padding-left: 4px;
}

.perm-tab-check {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #444;
  cursor: pointer;
}

.perm-export-check {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #1a73e8;
  font-weight: 600;
  cursor: pointer;
  padding-left: 4px;
}

.perm-form-actions {
  display: flex;
  gap: 10px;
  padding-top: 8px;
}
</style>
