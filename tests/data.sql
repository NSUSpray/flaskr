INSERT INTO user (username, password)
VALUES
  ('test', 'pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f'),
  ('other', 'pbkdf2:sha256:50000$kJPKsz6N$d2d4784f1b030a9761f5ccaeeaca413f27f2ecb76d6168407af962ddce849f79');

INSERT INTO post (title, body, tags, author_id, created)
VALUES
  ('test title 1', '*test***' || x'0a' || '# body', 'test_tag', 1, '2018-01-01 00:00:00'),
  ('test title 2', '', '', 1, '2018-01-01 00:00:00'),
  ('3', '', '', 1, '2018-01-01 00:00:00'),
  ('4', '', '', 1, '2018-01-01 00:00:00'),
  ('5', '', '', 1, '2018-01-01 00:00:00'),
  ('6', '', '', 1, '2018-01-01 00:00:00'),
  ('7', '', '', 1, '2018-01-01 00:00:00');

INSERT INTO reaction (post_id, user_id) VALUES (1, 1), (2, 1);

INSERT INTO comment (body, post_id, author_id, created)
VALUES
  ('test' || x'0a' || 'comment', 1, 1, '2018-01-01 00:00:00');
