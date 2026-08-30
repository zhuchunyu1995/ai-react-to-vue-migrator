/**
 * Python 后端传给 Node Runner 的请求结构。
 */
export interface AnalyzeRequest {
  action: "analyze";
  filename: string;
  source_code: string;
}

/**
 * React import 分析结果。
 */
export interface ImportAnalysis {
  // 导入来源，例如 react、axios、./UserCard.css
  source: string;

  // 当前文件中使用的本地变量名
  specifiers: string[];
}

/**
 * React Hook 分析结果。
 */
export interface HookAnalysis {
  // Hook 名称，例如 useState、useEffect
  name: string;

  // Hook 所在源码行号
  line: number | null;

  // useEffect/useMemo/useCallback 依赖数组长度
  // 没有依赖数组或者不是相关 Hook 时为 null
  dependency_count: number | null;
}

/**
 * Node Runner 最终返回的源码分析结果。
 */
export interface SourceAnalysis {
  filename: string;
  component_names: string[];
  imports: ImportAnalysis[];
  hooks: HookAnalysis[];
  props: string[];
  jsx_elements: string[];
  events: string[];
  has_default_export: boolean;
  warnings: string[];
}

/**
 * Node Runner 执行成功时的响应。
 */
export interface AnalyzeSuccessResponse {
  success: true;
  data: SourceAnalysis;
}

/**
 * Node Runner 执行失败时的响应。
 */
export interface AnalyzeErrorResponse {
  success: false;
  error: {
    type: string;
    message: string;
    line?: number;
    column?: number;
  };
}

export type AnalyzeResponse = AnalyzeSuccessResponse | AnalyzeErrorResponse;
