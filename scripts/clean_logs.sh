#!/bin/bash
# Log Cleanup Script for ScholarMind
# 日志清理脚本

set -e

echo "🧹 ScholarMind 日志清理工具"
echo "=============================="
echo ""

# 统计信息
LOGS_DIR="logs"
TOTAL_FILES=$(find "$LOGS_DIR" -type f 2>/dev/null | wc -l | tr -d ' ')
EMPTY_FILES=$(find "$LOGS_DIR" -type f -size 0 2>/dev/null | wc -l | tr -d ' ')
NON_EMPTY_FILES=$((TOTAL_FILES - EMPTY_FILES))
TOTAL_SIZE=$(du -sh "$LOGS_DIR" 2>/dev/null | cut -f1)

echo "📊 当前状态:"
echo "  - 总文件数: $TOTAL_FILES"
echo "  - 空文件数: $EMPTY_FILES"
echo "  - 有内容文件: $NON_EMPTY_FILES"
echo "  - 总大小: $TOTAL_SIZE"
echo ""

# 询问用户
read -p "是否清理所有空日志文件? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️  正在删除空日志文件..."
    find "$LOGS_DIR" -type f -size 0 -delete

    REMAINING=$(find "$LOGS_DIR" -type f 2>/dev/null | wc -l | tr -d ' ')
    echo "✅ 清理完成!"
    echo "  - 删除了 $EMPTY_FILES 个空文件"
    echo "  - 保留了 $REMAINING 个有内容的文件"

    NEW_SIZE=$(du -sh "$LOGS_DIR" 2>/dev/null | cut -f1)
    echo "  - 当前大小: $NEW_SIZE"
else
    echo "❌ 取消清理"
fi

echo ""
read -p "是否删除所有日志文件（包括有内容的）? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️  正在删除所有日志文件..."
    rm -rf "$LOGS_DIR"/*
    echo "✅ 所有日志文件已删除!"
else
    echo "❌ 保留有内容的日志文件"
fi

echo ""
echo "✨ 完成!"
