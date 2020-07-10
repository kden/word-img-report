<?xml version="1.0"?>

<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns="http://www.editeur.org/onix/2.1/reference/onix-international.dtd">
    <xsl:output method="xml" version="1.0" encoding="UTF-8" indent="yes"/>
    <xsl:strip-space elements="*"/>
    <xsl:template match="/onixFile">
        <ONIXMessage release="2.1">
            <Header>
                <FromCompany>Beneficient Technologies</FromCompany>
                <FromPerson>Math Export</FromPerson>
                <ToCompany>Benetech</ToCompany>
                <SentDate>201909012046</SentDate>
            </Header>
            <xsl:for-each select="onixRecords/onixRecord">
                <Product>
                    <xsl:call-template name="RecordReference">
                        <xsl:with-param name="productIdentifier" select="productIdentifier"/>
                        <xsl:with-param name="isbn" select="isbn"/>
                    </xsl:call-template>
                    <NotificationType>03</NotificationType>
                    <xsl:apply-templates select="isbn"/>
                    <xsl:apply-templates select="abcId"/>
                    <xsl:apply-templates select="externalIdentifierCode"/>
                    <xsl:apply-templates select="productIdentifier"/>
                    <xsl:call-template name="ProductForm">
                        <xsl:with-param name="onixRecordType" select="onixRecordType"/>
                    </xsl:call-template>
                    <xsl:call-template name="ProductFormDescription">
                        <xsl:with-param name="brailleCode" select="brailleCode"/>
                        <xsl:with-param name="brailleGrade" select="brailleGrade"/>
                    </xsl:call-template>
                    <xsl:apply-templates select="numberOfPages"/>
                    <xsl:apply-templates select="numberOfVolumes"/>
                    <xsl:apply-templates select="seriesTitle"/>
                    <xsl:apply-templates select="title"/>
                    <xsl:apply-templates select="englishTitle" />
                    <xsl:apply-templates select="edition"/>
                    <xsl:apply-templates select="contributors"/>
                    <xsl:apply-templates select="narratorName"/>
                    <xsl:apply-templates select="producer"/>
                    <xsl:call-template name="SupplyDetail">
                        <xsl:with-param name="supplier" select="supplier"/>
                        <xsl:with-param name="fundingSource" select="fundingSource"/>
                    </xsl:call-template>
                    <xsl:apply-templates select="languages"/>
                    <xsl:apply-templates select="bisacCategories"/>
                    <xsl:apply-templates select="contentWarnings"/>
                    <xsl:apply-templates select="externalCategoryCode"/>
                    <xsl:apply-templates select="publisherName"/>
                    <xsl:apply-templates select="countryOfPublication"/>
                    <xsl:apply-templates select="publicationDate"/>
                    <xsl:call-template name="CopyrightStatement">
                        <xsl:with-param name="copyrightYear" select="copyrightYear"/>
                        <xsl:with-param name="copyrightHolder" select="copyrightHolder"/>
                    </xsl:call-template>
                    <xsl:apply-templates select="gradeLow"/>
                    <xsl:apply-templates select="readingAgeLow"/>
                    <!-- In case we decide to support scheme code 06 -->
                    <!--
                    <xsl:apply-templates select="(lexileNumber|lexileCode)[1]"/>
                    -->
                    <xsl:apply-templates select="lexileCode"/>
                    <xsl:apply-templates select="lexileNumber"/>
                    <xsl:apply-templates select="relatedIsbns"/>
                    <xsl:apply-templates select="synopsis"/>
                    <xsl:apply-templates select="allowRecommendation"/>
                    <xsl:apply-templates select="instruments"/>
                    <xsl:apply-templates select="vocalParts"/>
                    <xsl:apply-templates select="opus"/>
                    <xsl:apply-templates select="musicKey"/>
                    <xsl:apply-templates select="musicScoreType"/>
                    <xsl:apply-templates select="chordSymbols"/>
                    <xsl:apply-templates select="brailleMusicScoreLayout"/>
                    <xsl:apply-templates select="notes"/>
                    <xsl:apply-templates select="movementTitle"/>
                    <xsl:apply-templates select="duration"/>
                    <xsl:apply-templates select="dateAdded"/>
                    <xsl:apply-templates select="countries"/>
                </Product>
            </xsl:for-each>
        </ONIXMessage>
    </xsl:template>

    <xsl:template name="RecordReference">
        <xsl:param name="productIdentifier"/>
        <xsl:param name="isbn"/>
        <xsl:if test="$productIdentifier != '' or $isbn != ''">
            <RecordReference>
                <xsl:choose>
                    <xsl:when test="$productIdentifier != ''">
                        <xsl:value-of select="$productIdentifier"/>
                    </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="$isbn"/>
                </xsl:otherwise>
                </xsl:choose>
            </RecordReference>
        </xsl:if>
    </xsl:template>

    <xsl:template match="isbn">
        <ProductIdentifier>
            <ProductIDType>15</ProductIDType>
            <IDValue>
                <xsl:value-of select="."/>
            </IDValue>
        </ProductIdentifier>
    </xsl:template>

    <xsl:template match="abcId">
        <ProductIdentifier>
            <ProductIDType>01</ProductIDType>
            <IDTypeName>ABC</IDTypeName> 
            <IDValue>
                <xsl:value-of select="."/>
            </IDValue>
        </ProductIdentifier>
    </xsl:template>

    <xsl:template match="externalIdentifierCode">
        <ProductIdentifier>
            <ProductIDType>01</ProductIDType>
            <IDTypeName>EXTERNAL_IDENTIFIER_CODE</IDTypeName> 
            <IDValue>
                <xsl:value-of select="."/>
            </IDValue>
        </ProductIdentifier>
    </xsl:template>

    <xsl:template match="productIdentifier">
        <ProductIdentifier>
            <ProductIDType>01</ProductIDType>
            <IDValue>
                <xsl:value-of select="."/>
            </IDValue>
        </ProductIdentifier>
    </xsl:template>
    
    <xsl:template name="ProductForm">
        <xsl:param name="onixRecordType"/>
        <xsl:choose>
            <xsl:when test="$onixRecordType='GENERIC'">
                <ProductContentType>10</ProductContentType>
                <ProductForm>DG</ProductForm>
            </xsl:when>
            <xsl:when test="$onixRecordType='BRAILLE_MUSIC'">
                <ProductContentType>11</ProductContentType>
                <ProductForm>DZ</ProductForm>
            </xsl:when>
            <xsl:when test="$onixRecordType='NARRATED_AUDIO'">
                <ProductForm>AA</ProductForm>
            </xsl:when>
        </xsl:choose>
    </xsl:template>

    <xsl:template name="ProductFormDescription">
        <xsl:param name="brailleCode"/>
        <xsl:param name="brailleGrade"/>
        <xsl:if test="$brailleCode != '' and $brailleGrade != ''">
            <ProductFormDescription>
                <xsl:value-of select="$brailleCode"/> Grade <xsl:value-of select="$brailleGrade"/>
            </ProductFormDescription>
        </xsl:if>
    </xsl:template>

    <xsl:template match="numberOfPages">
        <NumberOfPages>
            <xsl:value-of select="."/>
        </NumberOfPages>
    </xsl:template>

    <xsl:template match="numberOfVolumes">
        <NumberOfPieces>
            <xsl:value-of select="."/>
        </NumberOfPieces>
    </xsl:template>

    <xsl:template match="seriesTitle">
        <Series>
            <Title>
                <TitleType>01</TitleType>
                <TitleText>
                    <xsl:value-of select="."/>
                </TitleText>
            </Title>
            <xsl:apply-templates select="../seriesNumber"/>
        </Series>
    </xsl:template>

    <xsl:template match="seriesNumber">
        <NumberWithinSeries>
            <xsl:value-of select="."/>
        </NumberWithinSeries>
    </xsl:template>

    <xsl:template match="title">
        <Title>
            <TitleType>01</TitleType>
            <TitleText>
                <xsl:value-of select="."/>
            </TitleText>
            <xsl:apply-templates select="../subtitle"/>
        </Title>
    </xsl:template>

    <xsl:template match="englishTitle">
        <Title>
            <TitleType>06</TitleType>
            <TitleText>
                <xsl:value-of select="."/>
            </TitleText>
        </Title>
    </xsl:template>

    <xsl:template match="subtitle">
        <Subtitle>
            <xsl:value-of select="."/>
        </Subtitle>
    </xsl:template>

    <xsl:template match="edition">
        <EditionStatement>
            <xsl:value-of select="."/>
        </EditionStatement>
    </xsl:template>

    <xsl:template match="contributors">
        <xsl:for-each select="contributor">
            <Contributor>
                <SequenceNumber>
                    <xsl:number format="1"/>
                </SequenceNumber>
                <xsl:apply-templates select="contributorType"/>
                <PersonName>
                    <xsl:value-of select="name"/>
                </PersonName>
            </Contributor>
        </xsl:for-each>
    </xsl:template>

    <xsl:template match="contributorType">
        <ContributorRole>
            <xsl:choose>
                <xsl:when test=".='TRANSLATOR' or .='TRANSCRIBER'">B06</xsl:when>
                <xsl:when test=".='ARRANGER'">B25</xsl:when>
                <xsl:when test=".='COMPOSER'">A06</xsl:when>
                <xsl:when test=".='LYRICIST'">A05</xsl:when>
                <xsl:otherwise>A01</xsl:otherwise>
            </xsl:choose>
        </ContributorRole>
    </xsl:template>

    <xsl:template match="contentWarnings">
        <xsl:for-each select="contentWarning">
            <Audience>
                <AudienceCodeType>22</AudienceCodeType>
                <xsl:apply-templates select="."/>
            </Audience>
        </xsl:for-each>
    </xsl:template>

    <xsl:template match="contentWarning">
        <AudienceCodeValue>
            <xsl:choose>
                <xsl:when test=".='CONTENT_WARNING'">02</xsl:when>
                <xsl:when test=".='SEX'">03</xsl:when>
                <xsl:when test=".='VIOLENCE'">04</xsl:when>
                <xsl:when test=".='DRUGS'">05</xsl:when>
                <xsl:when test=".='LANGUAGE'">06</xsl:when>
                <xsl:when test=".='INTOLERANCE'">07</xsl:when>
                <xsl:otherwise>00</xsl:otherwise>
            </xsl:choose>
        </AudienceCodeValue>
    </xsl:template>

    <xsl:template match="narratorName">
        <Contributor>
            <SequenceNumber>
                <xsl:value-of select="count(../contributors/contributor) + 1"/>
            </SequenceNumber>
            <ContributorRole>E07</ContributorRole>
            <PersonName>
                <xsl:value-of select="."/>
            </PersonName>
            <xsl:apply-templates select="../narratorGender"/>
        </Contributor>
    </xsl:template>

    <xsl:template match="narratorGender">
        <ContributorDescription>
            <xsl:value-of select="translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')"/>
        </ContributorDescription>
    </xsl:template>

    <xsl:template match="producer">
        <Contributor>
            <SequenceNumber>
                <xsl:value-of select="count(../contributors/contributor) + count(../narratorName) + 1"/>
            </SequenceNumber>
            <ContributorRole>D01</ContributorRole>
            <PersonName>
                <xsl:value-of select="."/>
            </PersonName>
        </Contributor>
    </xsl:template>

    <xsl:template name="SupplyDetail">
        <xsl:param name="supplier"/>
        <xsl:param name="fundingSource"/>
        <xsl:if test="$supplier != '' or $fundingSource != ''">
            <SupplyDetail>
                <xsl:apply-templates select="$supplier"/>
                <xsl:apply-templates select="$fundingSource"/>
            </SupplyDetail>
        </xsl:if>
    </xsl:template>

    <xsl:template match="supplier">
        <SupplierIdentifier>
            <SupplierIDType>01</SupplierIDType>
            <IDTypeName>BKS_SUPPLIER</IDTypeName>
            <IDValue>
                <xsl:value-of select="."/>
            </IDValue>
        </SupplierIdentifier>
    </xsl:template>

    <xsl:template match="fundingSource">
        <SupplierIdentifier>
            <SupplierIDType>01</SupplierIDType>
            <IDTypeName>BKS_FUNDING</IDTypeName>
            <IDValue>
                <xsl:value-of select="."/>
            </IDValue>
        </SupplierIdentifier>
    </xsl:template>

    <xsl:template match="languages">
        <xsl:for-each select="language">
            <Language>
                <LanguageRole>01</LanguageRole>
                <LanguageCode><xsl:value-of select="."/></LanguageCode>
            </Language>
        </xsl:for-each>
    </xsl:template>

    <!-- Note this weird aspect of the ONIX specification, only the first BISAC
    category can be in a BASICMainSubject element, plus the use of "BASIC" looks like a typo, but it's not. -->
    <xsl:template match="bisacCategories">
        <xsl:for-each select="bisacCategory">
            <xsl:choose>
                <xsl:when test="position()=1">
                    <BASICMainSubject>
                        <xsl:value-of select="."/>
                    </BASICMainSubject>
                </xsl:when>
                <xsl:otherwise>
                    <Subject>
                        <SubjectSchemeIdentifier>10</SubjectSchemeIdentifier>
                        <SubjectCode>
                            <xsl:value-of select="."/>
                        </SubjectCode>
                    </Subject>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:for-each>
    </xsl:template>

    <xsl:template match="externalCategoryCode">
        <Subject>
            <SubjectSchemeIdentifier>24</SubjectSchemeIdentifier>
            <SubjectSchemeName>CELA</SubjectSchemeName>
            <SubjectCode>
                <xsl:value-of select="."/>
            </SubjectCode>
        </Subject>
    </xsl:template>

    <xsl:template name="CopyrightStatement">
        <xsl:param name="copyrightYear"/>
        <xsl:param name="copyrightHolder"/>
        <xsl:if test="$copyrightYear != '' or $copyrightHolder != ''">
            <CopyrightStatement>
                <xsl:apply-templates select="$copyrightYear"/>
                <xsl:apply-templates select="$copyrightHolder"/>
            </CopyrightStatement>
        </xsl:if>
    </xsl:template>

    <xsl:template match="copyrightYear">
        <CopyrightYear>
            <xsl:value-of select="."/>
        </CopyrightYear>
    </xsl:template>

    <xsl:template match="copyrightHolder">
        <CopyrightOwner>
            <PersonName>
                <xsl:value-of select="."/>
            </PersonName>
        </CopyrightOwner>
    </xsl:template>

    <xsl:template match="publisherName">
        <Publisher>
            <PublisherName>
                <xsl:value-of select="."/>
            </PublisherName>
        </Publisher>
    </xsl:template>

    <xsl:template match="countryOfPublication">
        <CountryOfPublication>
                <xsl:value-of select="."/>
        </CountryOfPublication>
    </xsl:template>

    <xsl:template match="publicationDate">
        <PublicationDate>
            <xsl:value-of select="."/>
        </PublicationDate>
    </xsl:template>

    <xsl:template match="gradeLow">
        <AudienceRange>
            <AudienceRangeQualifier>11</AudienceRangeQualifier>
            <AudienceRangePrecision>03</AudienceRangePrecision>
            <AudienceRangeValue>
                <xsl:value-of select="."/>
            </AudienceRangeValue>
            <xsl:apply-templates select="../gradeHigh"/>
        </AudienceRange>
    </xsl:template>

    <xsl:template match="gradeHigh">
        <AudienceRangePrecision>04</AudienceRangePrecision>
        <AudienceRangeValue>
            <xsl:value-of select="."/>
        </AudienceRangeValue>
    </xsl:template>

    <xsl:template match="readingAgeLow">
        <AudienceRange> 
            <AudienceRangeQualifier>17</AudienceRangeQualifier> 
            <AudienceRangePrecision>03</AudienceRangePrecision> 
            <AudienceRangeValue>
                <xsl:value-of select="."/>
            </AudienceRangeValue>
            <xsl:apply-templates select="../readingAgeHigh"/>
        </AudienceRange>
    </xsl:template>

    <xsl:template match="readingAgeHigh">
        <AudienceRangePrecision>04</AudienceRangePrecision> 
        <AudienceRangeValue>
            <xsl:value-of select="."/>
        </AudienceRangeValue>
    </xsl:template>

    <!-- In case we decide to support scheme code 06.  Replaces both lexileCode and lexileNumber templates -->
    <!--
    <xsl:template match="lexileNumber|lexileCode">
            <Complexity>
                <ComplexitySchemeIdentifier>06</ComplexitySchemeIdentifier>
                <ComplexityCode><xsl:value-of select="../lexileCode"/><xsl:value-of select="../lexileNumber"/></ComplexityCode>
            </Complexity>
    </xsl:template>
-->

    <xsl:template match="lexileCode">
        <Complexity>
            <ComplexitySchemeIdentifier>01</ComplexitySchemeIdentifier>
            <ComplexityCode><xsl:value-of select="."/></ComplexityCode>
        </Complexity>
    </xsl:template>

    <xsl:template match="lexileNumber">
        <Complexity>
            <ComplexitySchemeIdentifier>02</ComplexitySchemeIdentifier>
            <ComplexityCode><xsl:value-of select="."/></ComplexityCode>
        </Complexity>
    </xsl:template>

    <xsl:template match="duration">
        <Extent>
            <ExtentType>09</ExtentType>
            <ExtentValue>
                <xsl:value-of select="."/>
            </ExtentValue>
            <ExtentUnit>16</ExtentUnit>
        </Extent>
    </xsl:template>

    <xsl:template match="synopsis">
        <OtherText>
            <TextTypeCode>01</TextTypeCode>
            <TextFormat>02</TextFormat>
            <Text>
                <xsl:value-of select="."/>
            </Text>
        </OtherText>
    </xsl:template>
    
    <xsl:template match="allowRecommendation">
        <OtherText><!--Recommendation flag -->
            <TextTypeCode>32</TextTypeCode>
            <Text>
                <xsl:choose>
                    <xsl:when test=".='true'">Yes</xsl:when>
                    <xsl:otherwise>No</xsl:otherwise>
                </xsl:choose>
            </Text>
        </OtherText>
    </xsl:template>
    <xsl:template match="instruments">
        <OtherText>
            <TextTypeCode>100</TextTypeCode>
            <Text>
                <xsl:value-of select="."/>
            </Text>
        </OtherText>
    </xsl:template>
    <xsl:template match="vocalParts">
        <OtherText>
            <TextTypeCode>101</TextTypeCode>
            <Text>
                <xsl:value-of select="."/>
            </Text>
        </OtherText>
    </xsl:template>
    <xsl:template match="opus">
        <OtherText>
            <TextTypeCode>102</TextTypeCode>
            <Text>
                <xsl:value-of select="."/>
            </Text>
        </OtherText>
    </xsl:template>
    <xsl:template match="musicKey">
        <OtherText>
            <TextTypeCode>103</TextTypeCode>
            <Text>
                <xsl:value-of select="."/>
            </Text>
        </OtherText>
    </xsl:template>
    <xsl:template match="musicScoreType">
        <OtherText>
            <TextTypeCode>104</TextTypeCode>
            <Text>
                <xsl:value-of select="."/>
            </Text>
        </OtherText>
    </xsl:template>
    <xsl:template match="chordSymbols">
        <OtherText>
            <TextTypeCode>105</TextTypeCode>
            <Text>
                <xsl:choose>
                    <xsl:when test=".='true'">Yes</xsl:when>
                    <xsl:otherwise>No</xsl:otherwise>
                </xsl:choose>
            </Text>
        </OtherText>
    </xsl:template>
    <xsl:template match="brailleMusicScoreLayout">
        <OtherText>
            <TextTypeCode>106</TextTypeCode>
            <Text>
                <xsl:value-of select="."/>
            </Text>
        </OtherText>
    </xsl:template>
    <xsl:template match="notes">
        <OtherText>
            <TextTypeCode>110</TextTypeCode>
            <Text>
                <xsl:value-of select="."/>
            </Text>
        </OtherText>
    </xsl:template>
    <xsl:template match="movementTitle">
        <ContentItem>
            <ComponentTypeName>movement</ComponentTypeName>
            <xsl:apply-templates select="../movementNumber"/>
            <Title>
                <TitleType>01</TitleType>
                <TitleText>
                    <xsl:value-of select="."/>
                </TitleText>
            </Title>
        </ContentItem>
    </xsl:template>
    <xsl:template match="movementNumber">
        <ComponentTypeNumber>
            <xsl:value-of select="."/>
        </ComponentTypeNumber>
    </xsl:template>

    <xsl:template match="relatedIsbns">
        <xsl:for-each select="relatedIsbn">
            <RelatedProduct>
                <RelationCode>13</RelationCode>
                <ProductIdentifier>
                    <ProductIDType>15</ProductIDType>
                    <IDValue>
                        <xsl:value-of select="."/>
                    </IDValue>
                </ProductIdentifier>
            </RelatedProduct>
        </xsl:for-each>
    </xsl:template>

    <xsl:template match="dateAdded">
        <MarketRepresentation>
            <MarketDate>
                <!-- Custom role code, specific to Bookshare -->
                <MarketDateRole>03</MarketDateRole>
                <!-- Date added -->
                <Date>
                    <xsl:value-of select="."/>
                </Date>
            </MarketDate>
        </MarketRepresentation>
    </xsl:template>

    <xsl:template match="countries">
        <SalesRights>
            <SalesRightsType>01</SalesRightsType>
            <RightsCountry>
                <xsl:value-of select="country" separator="&#x20;"/>
            </RightsCountry>
        </SalesRights>
    </xsl:template>
</xsl:stylesheet>
