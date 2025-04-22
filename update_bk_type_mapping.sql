-- 检查表是否存在
USE stock_data;

-- 添加名称字段到bk_type_mapping表
ALTER TABLE `bk_type_mapping`
ADD COLUMN `名称` VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL AFTER `bk_code`;

-- 从capital_flow表填充名称数据
UPDATE `bk_type_mapping` bkt
JOIN (
    SELECT DISTINCT `代码`, `名称` 
    FROM `capital_flow` 
    WHERE `代码` LIKE 'BK%'
) cf ON bkt.`bk_code` = cf.`代码`
SET bkt.`名称` = cf.`名称`;

-- 创建名称索引以提高查询性能
CREATE INDEX idx_bk_name ON `bk_type_mapping`(`名称`);

-- 显示更新后的表结构
DESCRIBE `bk_type_mapping`; 