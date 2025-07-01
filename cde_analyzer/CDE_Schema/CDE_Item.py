# from typing import List, Optional, Union
# from datetime import date, datetime, time, timedelta
from typing import List, Optional
from pydantic import BaseModel, Field
from .classes import *


class CDEItem(BaseModel):
    x_id: Optional[str] = (
        None  # Field(alias="x_id", default=None) This field is defined in the API but no CDE has one.
    )
    nihEndorsed: Optional[bool]
    tinyId: Optional[str]
    x__v: Optional[int] = None  # Field(alias="x__v", default=None)
    elementType: Optional[str]
    archived: Optional[bool]
    views: Optional[int] = None
    sources: Optional[List[Source]]
    origin: Optional[str] = None
    imported: Optional[str] = None
    created: Optional[str] = None
    createdBy: Optional[CreatedBy]
    updated: Optional[str] = None
    updatedBy: Optional[UpdatedBy] = None
    stewardOrg: Optional[StewardOrg]
    usedByOrgs: Optional[List[str]] = None
    formElements: Optional[List[FormElement]] = None
    registrationState: Optional[RegistrationState]
    lastMigrationScript: Optional[str] = None
    designations: Optional[List[Designation]]
    definitions: Optional[List[Definition]]
    valueDomain: Optional[ValueDomain] = None
    classification: Optional[List[Classification]]
    referenceDocuments: Optional[List[ReferenceDocument]]
    properties: Optional[List[Property]]
    ids: Optional[List[Identifier]]
    attachments: Optional[List[Attachment]]
    comments: Optional[List[Comment]] = None
    dataSets: Optional[List[DataSet]] = None
    history: Optional[List[str]] = None
    derivationRules: Optional[List[DerivationRule]] = None
