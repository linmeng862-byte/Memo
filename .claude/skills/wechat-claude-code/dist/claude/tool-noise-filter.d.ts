/**
 * 工具噪音过滤器
 *
 * 某些 LLM 供应商（如 Z.ai 等聚合代理）会把服务端内置工具的输入/输出（JSON 参数、
 * URL、识别结果等）以文本形式塞进 `text_delta` 流。bridge 无法在协议层区分这些
 * 内容与 Claude 的正常旁白，于是会被原样推到微信，造成"全是代码"的灾难体验。
 *
 * 本模块用结构特征判定（不依赖任何 provider 签名），把命中段剥到只剩 Claude 的
 * 旁白，前面加上中性占位 `🔧 [工具调用]`。
 *
 * 设计文档：docs/superpowers/specs/2026-06-27-tool-noise-filter-design.md
 */
/**
 * 三条件 AND 判定：长度 > 阈值 + 含 ```json``` 围栏 + 含 URL 或绝对路径。
 * 任一不满足即原样返回。
 */
export declare function filterToolNoise(text: string): string;
