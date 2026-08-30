<script setup lang="ts">
import { computed, ref } from "vue";

const props = defineProps<{
  filename: string;
  sourceCode: string;
  busy: boolean;
  errorMessage: string;
}>();

const emit = defineEmits<{
  "update:filename": [value: string];
  "update:sourceCode": [value: string];
  "load-example": [value: "counter" | "userList"];
  clear: [];
  submit: [];
}>();

const selectedExample = ref("");

const lineCount = computed(() =>
  props.sourceCode ? props.sourceCode.split("\n").length : 0,
);

const characterCount = computed(() => props.sourceCode.length);

function chooseExample(event: Event) {
  const value = (event.target as HTMLSelectElement).value;
  selectedExample.value = value;
  if (value === "counter" || value === "userList") {
    emit("load-example", value);
  }
}
</script>

<template>
  <section class="source-panel" aria-labelledby="source-panel-title">
    <div class="panel-heading">
      <div>
        <p class="panel-index">01 / React Source</p>
        <h2 id="source-panel-title">输入待迁移组件</h2>
      </div>
      <span class="language-badge">TSX</span>
    </div>

    <div class="source-toolbar">
      <label class="filename-field">
        <span>文件名</span>
        <input
          :value="filename"
          type="text"
          autocomplete="off"
          placeholder="UserList.tsx"
          :disabled="busy"
          @input="emit('update:filename', ($event.target as HTMLInputElement).value)"
        />
      </label>

      <label class="example-field">
        <span>示例</span>
        <select :value="selectedExample" :disabled="busy" @change="chooseExample">
          <option value="" disabled>载入示例</option>
          <option value="counter">Counter</option>
          <option value="userList">UserList</option>
        </select>
      </label>

      <button class="clear-button" type="button" :disabled="busy" @click="emit('clear')">
        清空
      </button>
    </div>

    <div class="editor-shell" :aria-busy="busy">
      <div class="editor-topbar" aria-hidden="true">
        <span></span><span></span><span></span>
        <strong>{{ filename || "untitled.tsx" }}</strong>
      </div>
      <label class="sr-only" for="react-source">React 组件源码</label>
      <textarea
        id="react-source"
        :value="sourceCode"
        :disabled="busy"
        spellcheck="false"
        placeholder="在这里粘贴 React 函数组件源码…"
        :aria-describedby="errorMessage ? 'source-error' : 'source-hint'"
        @input="emit('update:sourceCode', ($event.target as HTMLTextAreaElement).value)"
      ></textarea>
      <div class="editor-footer">
        <span>UTF-8</span>
        <span>{{ lineCount }} 行 · {{ characterCount }} 字符</span>
      </div>
    </div>

    <p v-if="errorMessage" id="source-error" class="error-message" role="alert">
      {{ errorMessage }}
    </p>

    <div class="panel-actions">
      <p id="source-hint">不会直接生成代码，迁移计划需由你确认。</p>
      <button
        class="primary-button"
        type="button"
        :disabled="busy || !sourceCode.trim() || !filename.trim()"
        @click="emit('submit')"
      >
        <span v-if="busy" class="spinner" aria-hidden="true"></span>
        {{ busy ? "正在创建任务" : "分析并生成迁移计划" }}
        <span v-if="!busy" aria-hidden="true">→</span>
      </button>
    </div>
  </section>
</template>

<style scoped src="../../styles/source-input-panel.css"></style>
