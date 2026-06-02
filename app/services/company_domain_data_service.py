from typing import Annotated, BinaryIO

import pandas as pd
from fastapi import Depends

from app.schemas.column_mapping import ColumnMapping
from app.schemas.company_domain import CompanyDomainCreate


class CompanyDomainDataService:
    def get_df(self, file: BinaryIO) -> pd.DataFrame:
        return pd.read_excel(file, header=None).dropna(how="all")

    def process_df(self, df: pd.DataFrame, mapping: ColumnMapping, include_company_name: bool = True) -> pd.DataFrame:
        if mapping.domain_column is None:
            raise ValueError("domain_column is required")

        if mapping.has_header:
            df = df.iloc[1:].reset_index(drop=True)

        columns = [mapping.domain_column]
        if include_company_name and mapping.company_name_column is not None:
            columns.append(mapping.company_name_column)

        df = df.iloc[:, columns]
        df.columns = pd.RangeIndex(len(df.columns))

        return df

    def normalize_df_domains(self, df: pd.DataFrame, domain_col_index: int = 0) -> pd.DataFrame:
        df = df.dropna(subset=[domain_col_index])

        df[domain_col_index] = (
            df[domain_col_index]
            .astype(str)
            .str.strip()
            .str.lower()
            .str.replace(r"^https?://", "", regex=True)
            .str.replace(r"^www\.", "", regex=True)
            .str.replace(r"[^a-z0-9.-]", "", regex=True)
        )

        return df[df[domain_col_index].str.contains(r"\.", regex=True)]

    def normalize_df_names(self, df: pd.DataFrame, name_col_index: int = 1) -> pd.DataFrame:
        if name_col_index not in df.columns:
            return df

        df[name_col_index] = df[name_col_index].str.replace(r"[^\w\s&'\-.,()\/]", "", regex=True).str.strip()

        return df

    def subtract_sup_domains(
        self, nac_df: pd.DataFrame, sup_df: pd.DataFrame, domain_col_index: int = 0
    ) -> pd.DataFrame:
        return nac_df[~nac_df[domain_col_index].isin(sup_df[domain_col_index])]

    def build_company_domain_records(self, nac_df: pd.DataFrame) -> list[CompanyDomainCreate]:
        return [
            CompanyDomainCreate(domain=rec[0], name=None if pd.isna(v := rec.get(1)) else v or None)
            for rec in nac_df.to_dict(orient="records")
        ]


CompanyDomainDataServiceDep = Annotated[CompanyDomainDataService, Depends()]
