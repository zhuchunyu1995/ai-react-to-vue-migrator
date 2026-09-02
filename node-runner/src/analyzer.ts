import { parse, type ParserPlugin } from "@babel/parser";
import traverse from "@babel/traverse";
import * as t from "@babel/types";

interface ImportInfo {
  source: string;
  specifiers: string[];
  line: number | null;
}

interface HookInfo {
  name: string;
  code: string;
  dependencies: string[];
  line: number | null;
}

interface StateInfo {
  hook: "useState" | "useReducer";
  state_name: string | null;
  setter_name: string | null;
  initial_value: string | null;
  line: number | null;
}

interface PropInfo {
  name: string;
  line: number | null;
}

interface EventInfo {
  name: string;
  element: string;
  handler: string | null;
  line: number | null;
}

interface ReactAnalysisResult {
  filename: string;
  language: "javascript" | "typescript";
  component_name: string | null;

  imports: ImportInfo[];
  components: string[];
  hooks: HookInfo[];
  states: StateInfo[];
  props: PropInfo[];
  events: EventInfo[];

  jsx_elements: string[];
  list_renderings: string[];
  conditional_renderings: string[];
  exports: string[];

  warnings: string[];
}

/**
 * 根据文件扩展名选择 Babel Parser 插件。
 */
function getParserPlugins(filename: string): ParserPlugin[] {
  const lowerFilename = filename.toLowerCase();

  const isTypeScript =
    lowerFilename.endsWith(".ts") || lowerFilename.endsWith(".tsx");

  const containsJsx =
    lowerFilename.endsWith(".js") ||
    lowerFilename.endsWith(".jsx") ||
    lowerFilename.endsWith(".tsx");

  const plugins: ParserPlugin[] = [];

  if (isTypeScript) {
    plugins.push("typescript");
  }

  if (containsJsx) {
    plugins.push("jsx");
  }

  return plugins;
}

/**
 * 判断当前文件是否为 TypeScript。
 */
function getLanguage(filename: string): "javascript" | "typescript" {
  const lowerFilename = filename.toLowerCase();

  if (lowerFilename.endsWith(".ts") || lowerFilename.endsWith(".tsx")) {
    return "typescript";
  }

  return "javascript";
}

/**
 * 获取 AST 节点对应的源代码。
 */
function getNodeSource(node: t.Node, sourceCode: string): string {
  if (typeof node.start !== "number" || typeof node.end !== "number") {
    return "";
  }

  return sourceCode.slice(node.start, node.end).trim();
}

/**
 * 获取节点所在行号。
 */
function getNodeLine(node: t.Node): number | null {
  return node.loc?.start.line ?? null;
}

/**
 * 判断名称是否可能是 React 组件名。
 *
 * React 组件通常使用大写字母开头。
 */
function isComponentName(name: string): boolean {
  return /^[A-Z]/.test(name);
}

/**
 * 获取 JSX 标签名称。
 *
 * 支持：
 * div
 * UserCard
 * Form.Input
 */
function getJsxElementName(
  node: t.JSXIdentifier | t.JSXMemberExpression | t.JSXNamespacedName,
): string {
  if (t.isJSXIdentifier(node)) {
    return node.name;
  }

  if (t.isJSXMemberExpression(node)) {
    return `${getJsxElementName(node.object)}.${getJsxElementName(
      node.property,
    )}`;
  }

  return `${node.namespace.name}:${node.name.name}`;
}

/**
 * 从函数参数中提取 props。
 *
 * 例如：
 * function UserList({ users, loading }) {}
 */
function collectPropsFromParameters(
  parameters: Array<
    t.Identifier | t.Pattern | t.RestElement | t.TSParameterProperty
  >,
  props: PropInfo[],
): void {
  const firstParameter = parameters[0];

  if (!firstParameter) {
    return;
  }

  if (t.isObjectPattern(firstParameter)) {
    for (const property of firstParameter.properties) {
      if (t.isObjectProperty(property) && t.isIdentifier(property.key)) {
        props.push({
          name: property.key.name,
          line: getNodeLine(property),
        });
      }

      if (t.isRestElement(property) && t.isIdentifier(property.argument)) {
        props.push({
          name: `...${property.argument.name}`,
          line: getNodeLine(property),
        });
      }
    }

    return;
  }

  if (t.isIdentifier(firstParameter)) {
    props.push({
      name: firstParameter.name,
      line: getNodeLine(firstParameter),
    });
  }
}

/**
 * 提取 useEffect/useMemo 等 Hook 的依赖数组。
 */
function getHookDependencies(
  node: t.CallExpression,
  sourceCode: string,
): string[] {
  const dependencyArgument = node.arguments[1];

  if (!t.isArrayExpression(dependencyArgument)) {
    return [];
  }

  return dependencyArgument.elements
    .filter((element): element is t.Expression | t.SpreadElement => {
      return element !== null;
    })
    .map((element) => {
      return getNodeSource(element, sourceCode);
    });
}

/**
 * 根据文件名推断默认组件名。
 */
function getFilenameComponentName(filename: string): string | null {
  const basename = filename
    .split("/")
    .pop()
    ?.replace(/\.[^.]+$/, "");

  return basename || null;
}

/**
 * 分析 React 源代码。
 */
export function analyzeReactSource(
  filename: string,
  sourceCode: string,
): ReactAnalysisResult {
  const imports: ImportInfo[] = [];
  const components: string[] = [];
  const hooks: HookInfo[] = [];
  const states: StateInfo[] = [];
  const props: PropInfo[] = [];
  const events: EventInfo[] = [];

  const jsxElements = new Set<string>();
  const listRenderings: string[] = [];
  const conditionalRenderings: string[] = [];
  const exports: string[] = [];
  const warnings: string[] = [];

  let ast: ReturnType<typeof parse>;

  try {
    ast = parse(sourceCode, {
      sourceType: "unambiguous",
      plugins: getParserPlugins(filename),

      // 保留节点位置信息，后续生成行号。
      ranges: true,

      // 遇到部分可恢复错误时继续解析。
      errorRecovery: true,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);

    throw new Error(`React 源代码解析失败：${message}`);
  }

  /*
   * errorRecovery=true 时，部分错误会保存在 ast.errors。
   */
  for (const error of ast.errors) {
    warnings.push(error.message);
  }

  traverse(ast, {
    /*
     * 收集 import。
     */
    ImportDeclaration(path) {
      const specifiers = path.node.specifiers.map((specifier) => {
        if (t.isImportDefaultSpecifier(specifier)) {
          return specifier.local.name;
        }

        if (t.isImportNamespaceSpecifier(specifier)) {
          return `* as ${specifier.local.name}`;
        }

        if (t.isIdentifier(specifier.imported)) {
          return specifier.imported.name;
        }

        return specifier.imported.value;
      });

      imports.push({
        source: path.node.source.value,
        specifiers,
        line: getNodeLine(path.node),
      });
    },

    /*
     * 收集函数声明形式的组件。
     *
     * 例如：
     * function UserList() {}
     */
    FunctionDeclaration(path) {
      const componentName = path.node.id?.name;

      if (componentName && isComponentName(componentName)) {
        components.push(componentName);

        collectPropsFromParameters(path.node.params, props);
      }
    },

    /*
     * 收集变量形式组件，以及 useState/useReducer 状态。
     */
    VariableDeclarator(path) {
      const { id, init } = path.node;

      /*
       * const UserList = () => {}
       */
      if (
        t.isIdentifier(id) &&
        isComponentName(id.name) &&
        (t.isArrowFunctionExpression(init) || t.isFunctionExpression(init))
      ) {
        components.push(id.name);

        collectPropsFromParameters(init.params, props);
      }

      /*
       * const [keyword, setKeyword] = useState("")
       */
      if (
        t.isArrayPattern(id) &&
        t.isCallExpression(init) &&
        t.isIdentifier(init.callee) &&
        (init.callee.name === "useState" || init.callee.name === "useReducer")
      ) {
        const stateElement = id.elements[0];
        const setterElement = id.elements[1];

        states.push({
          hook: init.callee.name,
          state_name:
            stateElement && t.isIdentifier(stateElement)
              ? stateElement.name
              : null,
          setter_name:
            setterElement && t.isIdentifier(setterElement)
              ? setterElement.name
              : null,
          initial_value: init.arguments[0]
            ? getNodeSource(init.arguments[0], sourceCode)
            : null,
          line: getNodeLine(path.node),
        });
      }
    },

    /*
     * 收集所有 Hook 调用。
     */
    CallExpression(path) {
      const { node } = path;

      if (t.isIdentifier(node.callee) && /^use[A-Z]/.test(node.callee.name)) {
        hooks.push({
          name: node.callee.name,
          code: getNodeSource(node, sourceCode),
          dependencies: getHookDependencies(node, sourceCode),
          line: getNodeLine(node),
        });
      }

      /*
       * 收集 JSX 中的数组 map 渲染。
       *
       * 例如：
       * users.map(user => <li />)
       */
      if (
        t.isMemberExpression(node.callee) &&
        t.isIdentifier(node.callee.property, {
          name: "map",
        })
      ) {
        listRenderings.push(getNodeSource(node, sourceCode));
      }
    },

    /*
     * 收集 JSX 标签和事件。
     */
    JSXOpeningElement(path) {
      const elementName = getJsxElementName(path.node.name);

      jsxElements.add(elementName);

      for (const attribute of path.node.attributes) {
        if (
          !t.isJSXAttribute(attribute) ||
          !t.isJSXIdentifier(attribute.name)
        ) {
          continue;
        }

        const attributeName = attribute.name.name;

        /*
         * React 事件通常以 on 开头：
         * onClick、onChange、onSubmit。
         */
        if (/^on[A-Z]/.test(attributeName)) {
          let handler: string | null = null;

          if (
            t.isJSXExpressionContainer(attribute.value) &&
            !t.isJSXEmptyExpression(attribute.value.expression)
          ) {
            handler = getNodeSource(attribute.value.expression, sourceCode);
          }

          events.push({
            name: attributeName,
            element: elementName,
            handler,
            line: getNodeLine(attribute),
          });
        }
      }
    },

    /*
     * 收集三元表达式条件渲染。
     *
     * 例如：
     * loading ? <Loading /> : <List />
     */
    ConditionalExpression(path) {
      if (
        path.findParent((parentPath) => {
          return parentPath.isJSXExpressionContainer();
        })
      ) {
        conditionalRenderings.push(getNodeSource(path.node, sourceCode));
      }
    },

    /*
     * 收集 && 条件渲染。
     *
     * 例如：
     * loading && <Loading />
     */
    LogicalExpression(path) {
      if (
        path.node.operator === "&&" &&
        path.findParent((parentPath) => {
          return parentPath.isJSXExpressionContainer();
        })
      ) {
        conditionalRenderings.push(getNodeSource(path.node, sourceCode));
      }
    },

    /*
     * 收集默认导出。
     */
    ExportDefaultDeclaration(path) {
      exports.push(
        `default:${getNodeSource(path.node.declaration, sourceCode)}`,
      );
    },

    /*
     * 收集命名导出。
     */
    ExportNamedDeclaration(path) {
      if (path.node.declaration) {
        exports.push(getNodeSource(path.node.declaration, sourceCode));
      }

      for (const specifier of path.node.specifiers) {
        exports.push(getNodeSource(specifier, sourceCode));
      }
    },
  });

  /*
   * 去重，防止同一个组件被多次记录。
   */
  const uniqueComponents = [...new Set(components)];

  const uniqueProps = Array.from(
    new Map(props.map((prop) => [`${prop.name}:${prop.line}`, prop])).values(),
  );

  const componentName =
    uniqueComponents[0] ?? getFilenameComponentName(filename);

  if (uniqueComponents.length === 0) {
    warnings.push("没有识别到明确的 React 函数组件，组件名暂时根据文件名推断");
  }

  return {
    filename,
    language: getLanguage(filename),
    component_name: componentName,

    imports,
    components: uniqueComponents,
    hooks,
    states,
    props: uniqueProps,
    events,

    jsx_elements: [...jsxElements],
    list_renderings: listRenderings,
    conditional_renderings: conditionalRenderings,
    exports,

    warnings,
  };
}
