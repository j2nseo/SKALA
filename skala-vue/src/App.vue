<script setup>
import { RouterLink, RouterView } from 'vue-router'

import UnitToggler from './components/exercise/UnitToggler.vue'
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <RouterLink class="brand" to="/">
        <span class="brand-mark">W</span>
        Weatherly
      </RouterLink>

      <p class="sidebar-label">WEATHER DASHBOARD</p>

      <nav class="navigation">
        <RouterLink to="/"> <span>▦</span> 대시보드 </RouterLink>

        <RouterLink to="/about"> <span>◌</span> 서비스 소개 </RouterLink>

        <RouterLink to="/guide"> <span>✦</span> 생활 가이드 </RouterLink>
      </nav>

      <div class="sidebar-bottom">
        <p>온도 단위</p>
        <UnitToggler />
      </div>
    </aside>

    <div class="page-content">
      <RouterView />
    </div>
  </div>
</template>

<style>
* {
  box-sizing: border-box;
}

html,
body,
#app {
  min-height: 100%;
  margin: 0;
}

body {
  color: #25233a;
  font-family: 'Noto Sans KR', 'Apple SD Gothic Neo', sans-serif;
  background-color: #f7f6ff;
}

button,
input {
  font: inherit;
}

.app-shell {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  display: flex;
  position: sticky;
  top: 0;
  flex: 0 0 250px;
  flex-direction: column;
  min-height: 100vh;
  padding: 30px 20px;
  color: white;
  background:
    radial-gradient(circle at 0 100%, rgba(196, 181, 253, 0.35), transparent 34%),
    linear-gradient(165deg, #7c3aed, #5b21b6 56%, #402080);
}

.brand {
  display: flex;
  gap: 10px;
  align-items: center;
  color: white;
  font-size: 21px;
  font-weight: 800;
  letter-spacing: -0.7px;
  text-decoration: none;
}

.brand-mark {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  color: #6d28d9;
  font-size: 15px;
  background: white;
  border-radius: 11px;
}

.sidebar-label {
  margin: 50px 10px 14px;
  color: #ddd6fe;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 1.2px;
}

.navigation {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.navigation a {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 12px;
  color: #ede9fe;
  font-weight: 700;
  text-decoration: none;
  border-radius: 10px;
}

.navigation a:hover {
  color: white;
  background: rgba(255, 255, 255, 0.14);
}

.navigation a.router-link-exact-active {
  color: white;
  background: rgba(255, 255, 255, 0.2);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.12);
}

.sidebar-bottom {
  margin-top: auto;
  padding: 16px;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 14px;
}

.sidebar-bottom p {
  margin: 0 0 10px;
  color: #e9d5ff;
  font-size: 12px;
  font-weight: 700;
}

.page-content {
  flex: 1;
  min-width: 0;
}

@media (max-width: 760px) {
  .app-shell {
    display: block;
  }

  .sidebar {
    position: static;
    min-height: auto;
    padding: 20px;
  }

  .sidebar-label,
  .sidebar-bottom {
    display: none;
  }

  .navigation {
    flex-direction: row;
    flex-wrap: wrap;
    margin-top: 18px;
  }
}
</style>
