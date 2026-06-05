/**
 * 模糊搜索算法模块
 * ==================
 * 基于编辑距离（Levenshtein Distance）实现的字符串相似度搜索。
 *
 * 应用场景:
 *   - 搜索框输入时自动匹配最相似的主机名
 *   - 模糊查找列表中的项目
 *
 * 算法说明:
 *   莱文斯坦距离 = 将一个字符串变为另一个字符串所需的最少单字符编辑次数
 *   （编辑操作：替换、插入、删除）
 *   相似度 = 1 - (编辑距离 / 两字符串的最大长度)
 */

/**
 * 计算两个字符串的 Levenshtein（莱文斯坦）编辑距离
 *
 * 使用动态规划实现：
 *   - 时间复杂度: O(m * n)，m/n 分别为两字符串长度
 *   - 空间复杂度: O(m * n)
 *
 * 矩阵说明:
 *   matrix[i][j] = str1 前 i 个字符 → str2 前 j 个字符的最小编辑次数
 *
 * @param {string} str1 - 第一个字符串
 * @param {string} str2 - 第二个字符串
 * @returns {number}    - 编辑距离
 */
function levenshteinDistance(str1, str2) {
    const matrix = [];
    const len1 = str1.length;
    const len2 = str2.length;

    // 初始化矩阵边界：空字符串到另一个字符串的距离 = 另一个字符串的长度
    for (let i = 0; i <= len1; i++) {
        matrix[i] = [i];
    }
    for (let j = 0; j <= len2; j++) {
        matrix[0][j] = j;
    }

    // 逐格计算：取替换/插入/删除中的最小值
    for (let i = 1; i <= len1; i++) {
        for (let j = 1; j <= len2; j++) {
            if (str1.charAt(i - 1) === str2.charAt(j - 1)) {
                // 字符相同，无需编辑
                matrix[i][j] = matrix[i - 1][j - 1];
            } else {
                matrix[i][j] = Math.min(
                    matrix[i - 1][j - 1] + 1,   // 替换操作
                    matrix[i][j - 1] + 1,       // 插入操作
                    matrix[i - 1][j] + 1        // 删除操作
                );
            }
        }
    }
    return matrix[len1][len2];
}

/**
 * 计算两个字符串的相似度（忽略大小写）
 *
 * @param {string} str1 - 第一个字符串
 * @param {string} str2 - 第二个字符串
 * @returns {number}    - 相似度 (0 ~ 1)，1 表示完全相同，0 表示完全不同
 */
function similarity(str1, str2) {
    const distance = levenshteinDistance(
        str1.toLowerCase(),
        str2.toLowerCase()
    );
    const maxLength = Math.max(str1.length, str2.length);
    return maxLength === 0 ? 1 : 1 - (distance / maxLength);
}

/**
 * 从列表中查找与输入字符串相似的项
 *
 * 按相似度降序排序返回，只包含相似度 >= 阈值的项。
 *
 * @param {string} input     - 用户输入的搜索字符串
 * @param {string[]} list    - 待搜索的字符串列表
 * @param {number} threshold - 相似度阈值 (0~1)，默认 0.5
 * @returns {string[]}       - 按相似度降序排列的匹配结果
 */
function findSimilarStrings(input, list, threshold = 0.5) {
    // 过滤出相似度超过阈值的字符串，按相似度降序排列
    return list
        .filter(item => similarity(input, item) >= threshold)
        .sort((a, b) => similarity(input, b) - similarity(input, a));
}

export { levenshteinDistance, similarity, findSimilarStrings }
