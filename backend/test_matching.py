# import asyncio
# import sys
# sys.path.append('src')
# from services.matching_service import MatchingService

# async def test():
#     service = MatchingService()
#     patient_data = {'medical_query': 'I am a 45 year old woman with breast cancer'}
#     try:
#         result = await service.search_and_match_trials(patient_data, max_results=3, min_confidence=0.5)
#         print('SUCCESS: Found', len(result['matches']), 'matches')
#         if result['matches']:
#             for match in result['matches']:
#                 trial_id = match.get('trial_nct_id', 'Unknown')
#                 confidence = match.get('confidence_score', 0)
#                 print(f'Trial {trial_id}: {confidence} confidence')
#         else:
#             print('No matches found - metadata:')
#             metadata = result.get('processing_metadata', {})
#             print(f'Candidates: {metadata.get("total_candidates_evaluated", 0)}')
#             print(f'Finals: {metadata.get("final_matches_count", 0)}')
#     except Exception as e:
#         print('ERROR:', str(e))
#         import traceback
#         traceback.print_exc()

# if __name__ == "__main__":
#     asyncio.run(test())