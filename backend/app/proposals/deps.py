from typing import Annotated

from fastapi import Depends

from app.proposals.service import ProposalService
from app.theses.deps import ThesisRepoDep


def get_proposal_service(thesis_repo: ThesisRepoDep) -> ProposalService:
    return ProposalService(thesis_repo)


ProposalServiceDep = Annotated[ProposalService, Depends(get_proposal_service)]
