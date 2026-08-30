import path from "node:path";

import { parse, type ParserPlugin } from "@babel/parser";
import traverse from "@babel/traverse";
import * as t from "@babel/types";

import type { HookAnalysis, ImportAnalysis, SourceAnalysis } from "./types.js";

/**
 * 根据文件扩展名选择 Babel 解析插件。
 *
 * .js 和 .jsx：解析 JSX
 * .ts：解析 TypeScript
 * .tsx：同时解析 TypeScript 和 JSX
 */
function getParserPlugins(filename: string): ParserPlugin[] {
  const extension = path.extname(filename).toLowerCase();

  switch (extension) {
    case ".tsx":
      return ["typescript", "jsx"];

    case ".ts":
      return ["typescript"];

    case ".jsx":
    case ".js":
      return ["jsx"];

    default:
      throw new Error(`不支持的源码文件类型：${extension || "无扩展名"}`);
  }
}

/**
 * 判断名称是否可能是 React 组件名。
 *
 * React 组件通常以大写字母开头。
 */
function isComponentName(name: string): boolean {
  return /^[A-Z]/.test(name);
}

/**
 * 读取 JSX 标签名称。
 *
 * 支持：
 * div
 * UserCard
 * React.Fragment
 */
function getJsxElementName(
  node: t.JSXIdentifier | t.JSXMemberExpression | t.JSXNamespacedName,
): string {
  if (t.isJSXIdentifier(node)) {
    // <Button />   node 是 JSXIdentifier，name = 'Button'
    //  <HelloWorld />    // name = 'HelloWorld'
    // <div />           // name = 'div'
    return node.name;
  }

  if (t.isJSXMemberExpression(node)) {
    // <Button.Primary /> -> 'Button.Primary'
    return `${getJsxElementName(node.object)}.${node.property.name}`;
  }
  //  <svg:circle /> →  'svg:circle'
  return `${node.namespace.name}:${node.name.name}`;
}

/**
 * 读取函数调用名称。
 *
 * 支持：
 * useState()
 * React.useState()
 */
function getCallName(callee: t.CallExpression["callee"]): string | null {
  if (t.isIdentifier(callee)) {
    return callee.name;
  }
  //   React.useState()  → useState
  //   Array.isArray()   → isArray
  if (
    t.isMemberExpression(callee) &&
    !callee.computed &&
    t.isIdentifier(callee.property)
  ) {
    return callee.property.name;
  }

  return null;
}

/**
 * 从函数的解构参数中提取 Props。
 *
 * 例如：
 * function UserCard({ name, avatar }) {}
 *
 * 最终提取：
 * ["name", "avatar"]
 */
function collectPropsFromObjectPattern(
  pattern: t.ObjectPattern,
  props: Set<string>,
): void {
  for (const property of pattern.properties) {
    if (t.isObjectProperty(property)) {
      if (t.isIdentifier(property.key)) {
        props.add(property.key.name);
      } else if (t.isStringLiteral(property.key)) {
        props.add(property.key.value);
      }
    }

    if (t.isRestElement(property) && t.isIdentifier(property.argument)) {
      props.add(`...${property.argument.name}`);
    }
  }
}

/**
 * 使用 Babel AST 分析 React 源码。
 *
 * 注意：这里不返回完整 AST，只返回迁移工作流需要的摘要。
 */
export function analyzeReactSource(
  filename: string,
  sourceCode: string,
): SourceAnalysis {
  const ast = parse(sourceCode, {
    // 自动判断源码是 ES Module 还是普通 Script
    sourceType: "unambiguous",

    // 根据扩展名启用 JSX、TypeScript
    plugins: getParserPlugins(filename),
  });

  const componentNames = new Set<string>();
  const props = new Set<string>();
  const jsxElements = new Set<string>();
  const events = new Set<string>();
  const warnings = new Set<string>();

  const imports: ImportAnalysis[] = [];
  const hooks: HookAnalysis[] = [];

  let hasDefaultExport = false;

  traverse(ast, {
    /**
     * 分析 import。
     *
     * 例如：
     * import React, { useState } from "react"
     */
    ImportDeclaration(nodePath) {
      imports.push({
        source: nodePath.node.source.value,
        specifiers: nodePath.node.specifiers.map(
          (specifier) => specifier.local.name,
        ),
      });
    },

    /**
     * 分析函数声明形式的组件。
     *
     * 例如：
     * function UserCard({ name }) {}
     */
    FunctionDeclaration(nodePath) {
      const componentName = nodePath.node.id?.name;

      if (!componentName || !isComponentName(componentName)) {
        return;
      }

      componentNames.add(componentName);

      const firstParameter = nodePath.node.params[0];

      if (t.isObjectPattern(firstParameter)) {
        collectPropsFromObjectPattern(firstParameter, props);
      }
    },

    /**
     * 分析箭头函数形式的组件。
     *
     * 例如：
     * const UserCard = ({ name }) => {}
     */
    VariableDeclarator(nodePath) {
      if (!t.isIdentifier(nodePath.node.id)) {
        return;
      }

      const variableName = nodePath.node.id.name;
      const initializer = nodePath.node.init;

      if (
        !isComponentName(variableName) ||
        (!t.isArrowFunctionExpression(initializer) &&
          !t.isFunctionExpression(initializer))
      ) {
        return;
      }

      componentNames.add(variableName);

      const firstParameter = initializer.params[0];

      if (t.isObjectPattern(firstParameter)) {
        collectPropsFromObjectPattern(firstParameter, props);
      }
    },

    /**
     * 分析函数调用，识别 React Hook。
     *
     * 例如：
     * useState()
     * useEffect(() => {}, [userId])
     */
    CallExpression(nodePath) {
      const hookName = getCallName(nodePath.node.callee);

      if (!hookName || !/^use[A-Z0-9]/.test(hookName)) {
        return;
      }

      let dependencyCount: number | null = null;

      if (
        hookName === "useEffect" ||
        hookName === "useMemo" ||
        hookName === "useCallback"
      ) {
        const dependencies = nodePath.node.arguments[1];

        if (t.isArrayExpression(dependencies)) {
          dependencyCount = dependencies.elements.length;
        }
      }

      hooks.push({
        name: hookName,
        line: nodePath.node.loc?.start.line ?? null,
        dependency_count: dependencyCount,
      });
    },

    /**
     * 分析 props.xxx 访问形式。
     *
     * 例如：
     * props.name
     */
    MemberExpression(nodePath) {
      const { object, property, computed } = nodePath.node;

      if (
        t.isIdentifier(object, { name: "props" }) &&
        !computed &&
        t.isIdentifier(property)
      ) {
        props.add(property.name);
      }
    },

    /**
     * 分析 JSX 标签。
     *
     * 例如：
     * <div>
     * <UserCard>
     * <React.Fragment>
     */
    JSXOpeningElement(nodePath) {
      jsxElements.add(getJsxElementName(nodePath.node.name));

      for (const attribute of nodePath.node.attributes) {
        if (
          t.isJSXAttribute(attribute) &&
          t.isJSXIdentifier(attribute.name) &&
          /^on[A-Z]/.test(attribute.name.name)
        ) {
          events.add(attribute.name.name);
        }
      }
    },

    /**
     * 判断是否存在默认导出。
     */
    ExportDefaultDeclaration(nodePath) {
      hasDefaultExport = true;

      const declaration = nodePath.node.declaration;

      if (
        t.isFunctionDeclaration(declaration) &&
        declaration.id &&
        isComponentName(declaration.id.name)
      ) {
        componentNames.add(declaration.id.name);
      }
    },

    /**
     * 第一版暂不自动迁移 class 组件。
     * 发现 class 组件时添加风险提示。
     */
    ClassDeclaration(nodePath) {
      const superClass = nodePath.node.superClass;

      const extendsComponent =
        t.isIdentifier(superClass, { name: "Component" }) ||
        (t.isMemberExpression(superClass) &&
          t.isIdentifier(superClass.object, { name: "React" }) &&
          t.isIdentifier(superClass.property, { name: "Component" }));

      if (extendsComponent) {
        if (nodePath.node.id?.name) {
          componentNames.add(nodePath.node.id.name);
        }

        warnings.add("检测到 React class 组件，需要人工确认迁移方案");
      }
    },
  });

  if (componentNames.size === 0) {
    warnings.add("没有识别到明确的 React 组件名称");
  }

  return {
    filename,
    component_names: [...componentNames],
    imports,
    hooks,
    props: [...props],
    jsx_elements: [...jsxElements],
    events: [...events],
    has_default_export: hasDefaultExport,
    warnings: [...warnings],
  };
}
