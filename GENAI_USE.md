# Generative AI use and provenance

Fabric Reference Node permits the use of generative-AI tools as an engineering aid, but does not treat generated output as authoritative merely because a model produced it.

## Current project practice

Generative AI has been used in parts of the project's architecture synthesis, documentation, test planning, code review, refactoring proposals, grant/application drafting, and some code generation. Human maintainers remain responsible for understanding, reviewing, editing, testing, integrating, licensing, and accepting every contribution that enters the repository.

The current public genesis and conformance hardening were developed with assistance from OpenAI ChatGPT. The public runtime is backed by deterministic tests and CI; AI-generated statements do not substitute for those checks.

## Required boundaries

- A model output is not evidence of correctness, security, compliance, scientific truth, or institutional authority.
- Generated or AI-assisted code must pass the same review, tests, schema checks, licensing checks, and security scrutiny as human-written code.
- Machine `PASS` does not imply institutional `APPROVE`.
- Project documentation must distinguish verified repository evidence from hypotheses, targets, and external claims.
- Substantive AI-assisted contributions should disclose the model/tool and the role it played. Where a funder or upstream project requires a stricter provenance log, that requirement takes precedence.

## Funding/application provenance

For funding applications whose rules require prompt provenance, the project maintains a separate application log containing the model used, prompt dates/times, prompts, and required output examples or unedited outputs. Such logs may contain application-specific context and therefore are maintained separately from the default source tree unless public disclosure is required.

For NLnet applications, the project follows NLnet's current policy on the use of Generative Artificial Intelligence, including disclosure of GenAI use in proposal preparation and provenance logging as required by the application process.

## Contributor guidance

Contributors using generative AI should:

1. understand and review the resulting change;
2. verify that it can legally be contributed under the repository's Apache-2.0 license;
3. state substantive AI assistance in the pull request or commit context;
4. preserve relevant prompts/interactions when required by a grant, employer, upstream project, or contribution policy;
5. never use generated output to fabricate test, adoption, benchmark, security, or external-validation evidence.

This policy may become more structured as the project gains contributors and external funding requirements.
