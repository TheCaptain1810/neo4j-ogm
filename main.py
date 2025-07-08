from typing import ClassVar, Optional

from fastapi import FastAPI, HTTPException
from neontology import BaseNode, BaseRelationship, init_neontology

import os
from dotenv import load_dotenv
load_dotenv()


class TeamNode(BaseNode):
    __primaryproperty__: ClassVar[str] = "teamname"
    __primarylabel__: ClassVar[str] = "Team"
    teamname: str
    slogan: str = "Better than the rest!"


class TeamMemberNode(BaseNode):
    __primaryproperty__: ClassVar[str] = "nickname"
    __primarylabel__: ClassVar[str] = "TeamMember"
    nickname: str
    role: str


class BelongsTo(BaseRelationship):
    __relationshiptype__: ClassVar[str] = "BELONGS_TO"

    source: TeamMemberNode
    target: TeamNode


app = FastAPI()


@app.on_event("startup")
async def startup_event():
    init_neontology()


@app.get("/")
def read_root():
    return {"foo": "bar"}


@app.post("/teams/")
async def create_team(team: TeamNode):
    team.create()

    return team


@app.get("/teams/")
async def get_teams() -> list[TeamNode]:
    return TeamNode.match_nodes()


@app.get("/teams/{pp}")
async def get_team(pp: str) -> Optional[TeamNode]:
    return TeamNode.match(pp)


@app.delete("/teams/{pp}")
async def delete_team(pp: str):
    TeamNode.delete(pp)

    return {"message": "Team deleted successfully"}


@app.post("/team-members/")
async def create_team_member(member: TeamMemberNode, team_name: str):
    team = TeamNode.match(team_name)

    if team is None:
        raise HTTPException(status_code=404, detail="Team doesn't exist")

    member.create()

    rel = BelongsTo(source=member, target=team)
    rel.merge()

    return member


@app.get("/team-members/")
async def get_team_members() -> list[TeamMemberNode]:
    return TeamMemberNode.match_nodes()


@app.get("/team-members/{pp}")
async def get_team_member(pp: str) -> Optional[TeamMemberNode]:
    return TeamMemberNode.match(pp)


@app.delete("/team-members/{pp}")
async def delete_team_member(pp: str):
    TeamMemberNode.delete(pp)

    return {"message": "Team member deleted successfully"}
