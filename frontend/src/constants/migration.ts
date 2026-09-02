import type { MigrationStatus } from "@/types/migration";

export const migrationExamples = {
  counter: {
    filename: "Counter.tsx",
    source: `import React, { useState, useMemo, useEffect } from "react";

interface Product {
  id: number;
  name: string;
  price: number;
  inStock: boolean;
}

interface ProductListProps {
  products: Product[];
  discount?: number;
  children?: React.ReactNode;
}

const ProductList: React.FC<ProductListProps> = ({ 
  products, 
  discount = 0, 
  children 
}) => {
  const [search, setSearch] = useState("");
  const [showInStockOnly, setShowInStockOnly] = useState(false);

  // useMemo: 过滤 + 计算折扣价
  const filteredProducts = useMemo(() => {
    let result = products;
    if (showInStockOnly) {
      result = result.filter(p => p.inStock);
    }
    if (search.trim()) {
      result = result.filter(p => 
        p.name.toLowerCase().includes(search.toLowerCase())
      );
    }
    return result.map(p => ({
      ...p,
      finalPrice: p.price * (1 - discount)
    }));
  }, [products, search, showInStockOnly, discount]);

  // useMemo: 统计
  const stats = useMemo(() => ({
    total: filteredProducts.length,
    avgPrice: filteredProducts.length 
      ? filteredProducts.reduce((sum, p) => sum + p.finalPrice, 0) / filteredProducts.length 
      : 0
  }), [filteredProducts]);

  // useEffect: 日志
  useEffect(() => {
    console.log("显示 " + stats.total + " 个商品，平均价格: " + stats.avgPrice.toFixed(2));
  }, [stats]);

  return (
    <div className="product-list" style={{ padding: "16px", fontFamily: "sans-serif" }}>
      <h2>商品列表</h2>
      
      {children && <div style={{ marginBottom: "12px" }}>{children}</div>}
      
      <div style={{ display: "flex", gap: "8px", marginBottom: "12px", flexWrap: "wrap" }}>
        <input 
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="搜索商品..."
          style={{ flex: 1, padding: "6px 12px", border: "1px solid #ccc", borderRadius: "4px" }}
        />
        <button 
          onClick={() => setShowInStockOnly(!showInStockOnly)}
          style={{ 
            padding: "6px 16px", 
            background: showInStockOnly ? "#007bff" : "#e9ecef",
            color: showInStockOnly ? "white" : "#333",
            border: "none",
            borderRadius: "4px",
            cursor: "pointer"
          }}
        >
          {showInStockOnly ? "显示全部" : "只看有货"}
        </button>
      </div>

      <p style={{ fontSize: "14px", color: "#666" }}>
        共 {stats.total} 件商品，均价 ¥{stats.avgPrice.toFixed(2)}
      </p>

      {filteredProducts.length === 0 ? (
        <p style={{ textAlign: "center", color: "#999", padding: "20px" }}>
          没有匹配的商品
        </p>
      ) : (
        <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
          {filteredProducts.map(product => (
            <li 
              key={product.id}
              style={{
                display: "flex",
                justifyContent: "space-between",
                padding: "10px 12px",
                marginBottom: "6px",
                background: product.inStock ? "#f8f9fa" : "#fff3cd",
                borderRadius: "4px",
                border: "1px solid " + (product.inStock ? "#dee2e6" : "#ffc107")
              }}
            >
              <span>
                {product.name}
                {!product.inStock && (
                  <span style={{ marginLeft: "8px", fontSize: "12px", color: "#856404" }}>
                    (缺货)
                  </span>
                )}
              </span>
              <span style={{ fontWeight: "bold", color: "#28a745" }}>
                ¥{product.finalPrice.toFixed(2)}
                {discount > 0 && (
                  <span style={{ fontSize: "12px", color: "#dc3545", marginLeft: "6px" }}>
                    -{Math.round(discount * 100)}%
                  </span>
                )}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default ProductList;
`,
  },
  userList: {
    filename: "UserList.tsx",
    source: `import { useMemo, useState } from "react";

interface User {
  id: string;
  name: string;
}

export function UserList({ users }: { users: User[] }) {
  const [keyword, setKeyword] = useState("");
  const filteredUsers = useMemo(
    () => users.filter((user) => user.name.includes(keyword)),
    [users, keyword],
  );

  return (
    <section>
      <input
        value={keyword}
        onChange={(event) => setKeyword(event.target.value)}
      />
      <ul>
        {filteredUsers.map((user) => (
          <li key={user.id}>{user.name}</li>
        ))}
      </ul>
    </section>
  );
}`,
  },
};

export const migrationStatusMessages: Record<MigrationStatus, string> = {
  queued: "迁移任务已进入执行队列。",
  analyzing: "正在解析 React 源码和 AST。",
  analyzed: "React 源码分析完成。",
  planning: "源码分析完成，正在生成迁移计划。",
  planned: "迁移计划已经生成。",
  waiting_for_review: "迁移计划已生成，请确认后继续。",
  approved: "迁移计划已通过人工审核。",
  revision_requested: "修改意见已提交，准备重新生成迁移计划。",
  revising_plan: "AI 正在根据你的反馈修改迁移计划。",
  cancelled: "迁移任务已由用户终止。",
  rejected: "迁移计划已驳回，工作流已停止。",
  generating: "正在根据迁移计划生成 Vue 组件。",
  generated: "Vue 组件已经生成，准备执行工具链验证。",
  validating: "正在执行 SFC、ESLint、vue-tsc 与 Vite Build。",
  validated: "Vue 组件已通过全部工具链验证。",
  validation_failed: "工具链发现代码问题，准备自动修复。",
  repairing: "检查发现问题，正在尝试自动修复。",
  repaired: "代码已完成一轮自动修复，正在重新验证。",
  report_generated: "验证通过，迁移报告已经生成。",
  completed: "React 组件迁移已经完成。",
  failed: "迁移任务执行失败。",
};
