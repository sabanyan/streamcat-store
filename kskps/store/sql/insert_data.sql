INSERT INTO users (email, password, name) VALUES ('admin@kskp.io', '174db695f8aa0fece1329b27d70e8fc2359ad1060003eeb6cc6ad2fcafb95538', '管理者');
INSERT INTO users (email, password, name) VALUES ('dev@kskp.io', '1bdae10ff4532d6bd4c23d54cae62fa4f636b19cf5e3e8f83432a90aea99f33f', '開発用');
INSERT INTO users (email, password, name) VALUES ('grico@kskp.io', '63632217081179f5d4da82f3e1d357ea0c288574c5f74a8adc2fe81c7bc0bece', 'グリコ様用');

INSERT INTO projects (uuid, name, creator) VALUES ('a868644c-b97b-4ef9-aae0-f29f52973f92', '最初のテスト用プロジェクト', 0);
INSERT INTO projects (uuid, name, creator) VALUES ('09d1a654-1fce-466e-8a64-9bcf0ab7d40b', 'MCMDをひとまず動かしてみる', 0);
INSERT INTO projects (uuid, name, creator) VALUES ('0f7e62bc-3c9d-40d1-b17d-858a7a2d153f', 'グリコ様分析プロジェクト', 0);

INSERT INTO users_x_projects (user_id, project_id) VALUES (1, 1);
INSERT INTO users_x_projects (user_id, project_id) VALUES (1, 2);
INSERT INTO users_x_projects (user_id, project_id) VALUES (1, 3);
INSERT INTO users_x_projects (user_id, project_id) VALUES (2, 1);
INSERT INTO users_x_projects (user_id, project_id) VALUES (2, 2);
INSERT INTO users_x_projects (user_id, project_id) VALUES (3, 3);
