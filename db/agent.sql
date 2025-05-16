/*
 Navicat Premium Data Transfer

 Source Server         : mysql8
 Source Server Type    : MySQL
 Source Server Version : 80027
 Source Host           : localhost:3306
 Source Schema         : agent

 Target Server Type    : MySQL
 Target Server Version : 80027
 File Encoding         : 65001

 Date: 16/05/2025 13:56:00
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for captchas
-- ----------------------------
DROP TABLE IF EXISTS `captchas`;
CREATE TABLE `captchas`  (
  `id` int(0) NOT NULL AUTO_INCREMENT COMMENT '验证码记录的唯一标识',
  `code` varchar(10) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '验证码的具体值',
  `created_at` timestamp(0) NULL DEFAULT CURRENT_TIMESTAMP(0) COMMENT '验证码的创建时间',
  `used` tinyint(1) NULL DEFAULT 0 COMMENT '标记验证码是否已被使用',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 211 CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = '存储验证码信息的表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of captchas
-- ----------------------------
INSERT INTO `captchas` VALUES (1, 'SWE2', '2025-04-15 17:59:38', 0);

-- ----------------------------
-- Table structure for users
-- ----------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users`  (
  `id` int(0) NOT NULL AUTO_INCREMENT COMMENT '用户ID，唯一标识每个用户',
  `username` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '用户名，必须唯一',
  `hashed_password` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '用户密码的哈希值',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `username`(`username`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 2 CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = '存储用户信息的表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of users
-- ----------------------------
INSERT INTO `users` VALUES (1, 'testuser', '$2b$12$AqtfzbN4heEufBfIAavv9uvcOdxBBDkojkK3xo/Dpuwl2JLolwsXO');
INSERT INTO `users` VALUES (2, 'testuser1', '$2b$12$YMjOZmJjhhFKvvKGECdzt.IGTkQ9RSu5N52llzVyyCGt69rcNEoyS');

SET FOREIGN_KEY_CHECKS = 1;
