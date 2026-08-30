<template>
  <header class="app-header">
    <div class="header-inner">
      <a class="brand" href="/" aria-label="返回迁移工作台首页">
        <span class="brand-mark" aria-hidden="true">
          <span>R</span>
          <i>→</i>
          <span>V</span>
        </span>
        <span class="brand-copy">
          <strong>Bridge AI</strong>
          <small>React → Vue Migration</small>
        </span>
      </a>

      <nav aria-label="首页导航">
        <a href="#workspace">迁移工作台</a>
        <span class="version-badge">MVP · Local</span>
      </nav>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  position: sticky;
  top: 0;
  z-index: 10;
  border-bottom: 1px solid rgba(217, 226, 238, 0.82);
  background: rgba(247, 249, 252, 0.88);
  backdrop-filter: blur(18px);
}

.header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: min(1180px, calc(100% - 40px));
  min-height: 68px;
  margin: 0 auto;
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  color: inherit;
  text-decoration: none;
}

.brand-mark {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 8px 10px;
  border: 1px solid var(--border-strong);
  border-radius: 11px;
  background: var(--surface);
  box-shadow: var(--shadow-sm);
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 800;
}

.brand-mark span:first-child {
  color: var(--react);
}

.brand-mark span:last-child {
  color: var(--vue);
}

.brand-mark i {
  color: var(--text-muted);
  font-style: normal;
}

.brand-copy {
  display: grid;
  gap: 2px;
}

.brand-copy strong {
  color: var(--text-strong);
  font-size: 14px;
  letter-spacing: -0.01em;
}

.brand-copy small {
  color: var(--text-muted);
  font-size: 10px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

nav {
  display: flex;
  align-items: center;
  gap: 22px;
}

nav a {
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 650;
  text-decoration: none;
}

nav a:hover {
  color: var(--primary);
}

.version-badge {
  padding: 7px 10px;
  border: 1px solid rgba(15, 159, 110, 0.2);
  border-radius: 999px;
  background: rgba(15, 159, 110, 0.08);
  color: #087654;
  font-size: 10px;
  font-weight: 750;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

@media (max-width: 680px) {
  .header-inner {
    width: min(100% - 24px, 1180px);
  }

  .brand-copy small,
  nav a {
    display: none;
  }
}
</style>
