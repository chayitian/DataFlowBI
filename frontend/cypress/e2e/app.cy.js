describe("dataflowbi", () => {
  it("uploads and renders analytics", () => {
    cy.visit("/");
    cy.get('input[type="file"]').selectFile("cypress/fixtures/sample.csv", { force: true });
    cy.contains("button", /开始解析|Parse data/).click();
    cy.get(".selection-overlay .primary-btn").first().click();

    cy.get(".hero-card").should("be.visible");
    cy.get(".chart-canvas").should("be.visible");

    cy.contains("button", /数据筛选|Data Filter/).click();
    cy.get(".selection-overlay .primary-btn").first().click();

    cy.intercept("POST", "**/export/docx").as("exportDocx");
    cy.contains("button", /导出 Word|Export Word/).click();
    cy.wait("@exportDocx");
  });
});
