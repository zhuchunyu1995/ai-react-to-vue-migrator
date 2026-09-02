import js from "@eslint/js";
import pluginVue from "eslint-plugin-vue";
import globals from "globals";
import tseslint from "typescript-eslint";

export default tseslint.config(
  {
    ignores: ["dist/**", ".validation-workspaces/**/dist/**"],
  },

  js.configs.recommended,

  ...tseslint.configs.recommended,

  // 使用 Vue 3 基础错误检查规则。
  ...pluginVue.configs["flat/essential"],

  {
    files: ["**/*.vue", "**/*.ts"],

    languageOptions: {
      sourceType: "module",

      globals: {
        ...globals.browser,
        ...globals.es2022,
      },

      parserOptions: {
        // .vue 内部的 TypeScript 交给 TS Parser。
        parser: tseslint.parser,
        extraFileExtensions: [".vue"],
      },
    },

    rules: {
      // 生成的单文件组件允许单个单词名称。
      "vue/multi-word-component-names": "off",

      // MVP 阶段暂时允许 any。
      "@typescript-eslint/no-explicit-any": "off",
    },
  },
);
