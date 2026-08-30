from pydantic import BaseModel, Field


class ImportAnalysis(BaseModel):
    """React import 分析结果。"""

    # 导入来源，例如 react、axios
    source: str

    # 当前文件中的本地变量名称
    specifiers: list[str] = Field(default_factory=list)


class HookAnalysis(BaseModel):
    """React Hook 分析结果。"""

    # Hook 名称，例如 useState、useEffect
    name: str

    # Hook 所在的源码行号
    line: int | None = None

    # useEffect/useMemo/useCallback 的依赖数组长度
    dependency_count: int | None = None


class SourceAnalysis(BaseModel):
    """Node Runner 返回的 React 源码分析结果。"""

    filename: str

    # 分析出来的 React 组件名称
    component_names: list[str] = Field(default_factory=list)

    # import 信息
    imports: list[ImportAnalysis] = Field(default_factory=list)

    # React Hook 信息
    hooks: list[HookAnalysis] = Field(default_factory=list)

    # 组件 Props
    props: list[str] = Field(default_factory=list)

    # JSX 中出现的标签
    jsx_elements: list[str] = Field(default_factory=list)

    # JSX 中出现的事件，例如 onClick
    events: list[str] = Field(default_factory=list)

    # 是否存在 export default
    has_default_export: bool = False

    # 需要人工确认的风险
    warnings: list[str] = Field(default_factory=list)
