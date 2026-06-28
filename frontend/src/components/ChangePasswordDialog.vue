<script setup>
import { reactive, ref, watch } from "vue";

const props = defineProps({
  visible: { type: Boolean, default: false },
  username: { type: String, default: "" },
});

const emit = defineEmits(["close", "password-changed"]);

const loading = ref(false);
const errorMsg = ref("");

const form = reactive({
  currentPassword: "",
  newPassword: "",
  confirmPassword: "",
});

function resetForm() {
  form.currentPassword = "";
  form.newPassword = "";
  form.confirmPassword = "";
  errorMsg.value = "";
}

watch(() => props.visible, (visible) => {
  if (visible) {
    resetForm();
  }
});

async function submitForm() {
  errorMsg.value = "";

  if (!form.currentPassword || !form.newPassword || !form.confirmPassword) {
    errorMsg.value = "请完整填写密码信息";
    return;
  }
  if (form.newPassword.length < 8) {
    errorMsg.value = "新密码至少需要 8 位";
    return;
  }
  if (form.newPassword !== form.confirmPassword) {
    errorMsg.value = "两次输入的新密码不一致";
    return;
  }

  loading.value = true;
  try {
    const token = localStorage.getItem("auth_token") || "";
    const res = await fetch("/api/auth/change-password", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        current_password: form.currentPassword,
        new_password: form.newPassword,
      }),
    });
    const body = await res.json();
    if (!res.ok) {
      const raw = body.detail || body.message;
      errorMsg.value = !raw ? "修改密码失败"
        : typeof raw === "string" ? raw
        : Array.isArray(raw) ? raw.map((e) => e?.msg || JSON.stringify(e)).join("; ")
        : JSON.stringify(raw);
      return;
    }
    resetForm();
    emit("password-changed", body.message || "密码已修改，请重新登录");
  } catch {
    errorMsg.value = "网络错误，请重试";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <teleport to="body">
    <div v-if="visible" class="pwd-overlay" @click.self="emit('close')">
      <div class="pwd-dialog">
        <div class="pwd-header">
          <div>
            <div class="pwd-title">修改密码</div>
            <div class="pwd-subtitle">账号固定不可修改，仅支持更新当前登录账号的密码。</div>
          </div>
          <button class="pwd-close" type="button" @click="emit('close')">×</button>
        </div>

        <div class="pwd-form">
          <label class="pwd-field">
            <span>账号</span>
            <input :value="username" type="text" disabled />
          </label>
          <label class="pwd-field">
            <span>当前密码</span>
            <input v-model="form.currentPassword" type="password" autocomplete="current-password" />
          </label>
          <label class="pwd-field">
            <span>新密码</span>
            <input v-model="form.newPassword" type="password" autocomplete="new-password" />
          </label>
          <label class="pwd-field">
            <span>确认新密码</span>
            <input v-model="form.confirmPassword" type="password" autocomplete="new-password" />
          </label>
          <div v-if="errorMsg" class="pwd-error">{{ errorMsg }}</div>
        </div>

        <div class="pwd-actions">
          <button class="pwd-btn secondary" type="button" @click="emit('close')">取消</button>
          <button class="pwd-btn primary" type="button" :disabled="loading" @click="submitForm">
            {{ loading ? "提交中..." : "确认修改" }}
          </button>
        </div>
      </div>
    </div>
  </teleport>
</template>

<style scoped>
.pwd-overlay {
  position: fixed;
  inset: 0;
  z-index: 2100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(15, 23, 42, 0.5);
  backdrop-filter: blur(4px);
}

.pwd-dialog {
  width: min(100%, 440px);
  border-radius: 18px;
  background: #ffffff;
  box-shadow: 0 24px 64px rgba(15, 23, 42, 0.25);
  overflow: hidden;
}

.pwd-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 24px 24px 12px;
}

.pwd-title {
  font-size: 20px;
  font-weight: 700;
  color: #0f172a;
}

.pwd-subtitle {
  margin-top: 6px;
  font-size: 13px;
  line-height: 1.5;
  color: #64748b;
}

.pwd-close {
  border: none;
  background: transparent;
  color: #475569;
  font-size: 28px;
  line-height: 1;
  cursor: pointer;
}

.pwd-form {
  display: grid;
  gap: 14px;
  padding: 8px 24px 0;
}

.pwd-field {
  display: grid;
  gap: 6px;
}

.pwd-field span {
  font-size: 13px;
  font-weight: 600;
  color: #334155;
}

.pwd-field input {
  height: 42px;
  border: 1px solid #dbe4f0;
  border-radius: 10px;
  padding: 0 12px;
  font-size: 14px;
  color: #0f172a;
  outline: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.pwd-field input:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
}

.pwd-field input:disabled {
  background: #f8fafc;
  color: #64748b;
  cursor: not-allowed;
}

.pwd-error {
  border-radius: 10px;
  background: #fef2f2;
  color: #b91c1c;
  padding: 10px 12px;
  font-size: 13px;
}

.pwd-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 24px 24px;
}

.pwd-btn {
  height: 40px;
  min-width: 96px;
  border-radius: 10px;
  border: none;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

.pwd-btn.primary {
  background: #2563eb;
  color: #ffffff;
}

.pwd-btn.secondary {
  background: #e2e8f0;
  color: #0f172a;
}

.pwd-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
