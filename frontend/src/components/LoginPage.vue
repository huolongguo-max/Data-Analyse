<script setup>
import { ref } from "vue";

const emit = defineEmits(["login-success"]);

const username = ref("");
const password = ref("");
const errorMsg = ref("");
const loading = ref(false);

async function handleLogin() {
  if (!username.value || !password.value) {
    errorMsg.value = "请输入账号和密码";
    return;
  }
  loading.value = true;
  errorMsg.value = "";
  try {
    const form = new URLSearchParams();
    form.append("username", username.value);
    form.append("password", password.value);
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form.toString(),
    });
    const body = await res.json();
    if (!res.ok) {
      const raw = body.detail || body.message;
      errorMsg.value = !raw ? "登录失败"
        : typeof raw === "string" ? raw
        : Array.isArray(raw) ? raw.map((e) => e?.msg || JSON.stringify(e)).join("; ")
        : JSON.stringify(raw);
      return;
    }
    localStorage.setItem("auth_token", body.access_token);
    localStorage.setItem("auth_user", JSON.stringify({
      username: body.username,
      role: body.role,
      permissions: body.permissions || {},
    }));
    emit("login-success", {
      username: body.username,
      role: body.role,
      permissions: body.permissions || {},
    });
  } catch {
    errorMsg.value = "网络错误，请重试";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="login-shell">
    <div class="login-card">
      <div class="login-logo">
        <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
          <rect width="36" height="36" rx="10" fill="#1a73e8"/>
          <path d="M9 18h18M18 9v18" stroke="#fff" stroke-width="2.5" stroke-linecap="round"/>
        </svg>
      </div>
      <h1 class="login-title">储备数据可视化看板</h1>
      <p class="login-sub">请使用内部账号登录</p>

      <form class="login-form" @submit.prevent="handleLogin">
        <div class="login-field">
          <label>账号</label>
          <input v-model="username" type="text" placeholder="请输入账号" autocomplete="username" />
        </div>
        <div class="login-field">
          <label>密码</label>
          <input v-model="password" type="password" placeholder="请输入密码" autocomplete="current-password" />
        </div>
        <div v-if="errorMsg" class="login-error">{{ errorMsg }}</div>
        <button type="submit" class="login-btn" :disabled="loading">
          {{ loading ? "登录中..." : "登录" }}
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.login-shell {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
}

.login-card {
  width: 100%;
  max-width: 380px;
  background: #fff;
  border-radius: 16px;
  padding: 40px 36px 36px;
  box-shadow: 0 8px 40px rgba(0,0,0,0.25);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.login-logo { margin-bottom: 4px; }

.login-title {
  font-size: 18px;
  font-weight: 700;
  color: #1a1a2e;
  text-align: center;
}

.login-sub {
  font-size: 13px;
  color: #888;
  margin-bottom: 12px;
}

.login-form {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-top: 8px;
}

.login-field {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.login-field label {
  font-size: 13px;
  font-weight: 600;
  color: #444;
}

.login-field input {
  padding: 9px 12px;
  border: 1px solid #dde1ea;
  border-radius: 7px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.15s;
}

.login-field input:focus {
  border-color: #1a73e8;
  box-shadow: 0 0 0 3px rgba(26,115,232,0.12);
}

.login-error {
  font-size: 13px;
  color: #d93025;
  background: #fce8e6;
  padding: 8px 12px;
  border-radius: 6px;
}

.login-btn {
  width: 100%;
  height: 42px;
  background: #1a73e8;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
  margin-top: 4px;
}

.login-btn:hover:not(:disabled) { background: #1557b0; }
.login-btn:disabled { opacity: 0.65; cursor: not-allowed; }
</style>
