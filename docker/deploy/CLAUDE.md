# deploy/
> L2 | 父级: docker/

生产环境部署配置文件

openresty-skill.conf: OpenResty 反向代理配置，skill.askdao.ai 域名，HTTPS/SSL + WebSocket/SSE，upstream 使用 Docker 容器名（需 network connect），部署到 /opt/1panel/www/conf.d/

# 1. 部署
cp /home/skill-compose/docker/deploy/openresty-skill.conf /opt/1panel/www/conf.d/skill.askdao.ai.conf


[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
