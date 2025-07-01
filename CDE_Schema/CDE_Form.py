from typing import List, Optional
from pydantic import BaseModel, Field
from .classes import (
    Attachment,
    CDE,
    Classification,
    ClassificationScheme,
    Comment,
    Context,
    Copyright,
    CreatedBy,
    DataSet,
    DatatypeDate,
    DatatypeDynamicCodeList,
    DatatypeExternallyDefined,
    DatatypeNumber,
    DatatypeText,
    DatatypeTime,
    DatatypeValueList,
    Definition,
    DerivationRule,
    Designation,
    DisplayProfile,
    Element,
    ElementInner,
    Form,
    FormElement,
    FormCopyright,
    Identifier,
    InForm,
    Instruction,
    MergedTo,
    PermissibleValue,
    Property,
    Protocol,
    Question,
    ReferenceDocument,
    RegistrationState,
    ReplacedBy,
    Reply,
    SkipLogic,
    Source,
    StewardOrg,
    Tag,
    UnitOfMeasure,
    UpdatedBy,
    UploadedBy,
    ValueDomain,
)


class CDEForm(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    nihEndorsed: Optional[bool]
    tinyId: Optional[str]
    version: Optional[str] = None
    elementType: Optional[str]
    archived: Optional[bool]
    changeNote: Optional[str] = None
    comments: Optional[List[Comment]] = None
    copyright: Optional[FormCopyright]
    created: Optional[str] = None
    createdBy: Optional[CreatedBy]
    elementType: Optional[str]
    imported: Optional[str] = None
    isCopyrighted: Optional[bool] = None
    lastMigrationScript: Optional[str] = None
    noRenderAllowed: Optional[bool] = None
    origin: Optional[str] = None
    registrationState: Optional[RegistrationState]
    sources: Optional[List[Source]]
    stewardOrg: Optional[StewardOrg]
    updated: Optional[str] = None
    updatedBy: Optional[UpdatedBy] = None
    formElements: Optional[List[FormElement]]
    designations: Optional[List[Designation]]
    definitions: Optional[List[Definition]]
    classification: Optional[List[Classification]] = None
    referenceDocuments: Optional[List[ReferenceDocument]]
    displayProfiles: Optional[List[DisplayProfile]]
    properties: Optional[List[Property]]
    ids: Optional[List[Identifier]]
    cdeTinyIds: Optional[List[str]]
    attachments: Optional[List[Attachment]]
    history: Optional[List[str]] = None
